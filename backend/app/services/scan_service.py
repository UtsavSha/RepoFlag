# <-- Make sure File is imported
from app.models import Scan, ScanStatus, Finding, File
import os
import shutil
import tempfile
import stat
from git import Repo
from sqlalchemy.orm import Session
from datetime import datetime
import time

from app.models import Scan, ScanStatus, Finding
from app.risk_engine.scoring import calculate_risk_score
from app.scanners.bandit import run_bandit
from app.scanners.gitleaks import run_gitleaks           # <-- Import Gitleaks
from app.analyzers.git_history import analyze_git_history  # <-- Import Intelligence
from app.scanners.semgrep import run_semgrep
from app.risk_engine.file_risk import calculate_file_risk
from app.analyzers.complexity import analyze_complexity


def force_remove_readonly(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    func(path)


def execute_scan_pipeline(scan_id: int, repo_url: str, db: Session):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        return

    scan.status = ScanStatus.RUNNING
    db.commit()

    repo_dir = tempfile.mkdtemp(prefix=f"auspex_scan_{scan_id}_")

    try:
        print(f"Cloning {repo_url}...")
        Repo.clone_from(repo_url, repo_dir)

        # ==========================================
        # 1. RUN INTELLIGENCE ANALYZERS
        # ==========================================
        history_stats = analyze_git_history(repo_dir)
        complexity_stats = analyze_complexity(repo_dir)  # <-- ADD THIS

        # ==========================================
        # 2. POPULATE THE 'FILES' TABLE IN DATABASE
        # ==========================================
        file_map = {}

        # Combine all known files from history AND complexity
        all_known_files = set([h["file"]
                              for h in history_stats.get("hotspots", [])])
        all_known_files.update(complexity_stats.keys())

        for f_path in all_known_files:
            # Find the commit changes if it exists in hotspots
            changes = next((h["changes"] for h in history_stats.get(
                "hotspots", []) if h["file"] == f_path), 1)

            db_file = File(
                repository_id=scan.repository_id,
                file_path=f_path,
                commit_count=changes,
                author_count=history_stats.get("unique_authors", 1),
                complexity_score=complexity_stats.get(
                    f_path, 0.0)  # <-- ADD THIS
            )
            db.add(db_file)
            db.flush()
            file_map[f_path] = db_file

        # 3. Run Security Scanners
        all_findings = []

        bandit_results = run_bandit(repo_dir)
        gitleaks_results = run_gitleaks(repo_dir)
        semgrep_results = run_semgrep(repo_dir)  # <-- ADD THIS LINE

        all_findings.extend(bandit_results)
        all_findings.extend(gitleaks_results)
        all_findings.extend(semgrep_results)    # <-- ADD THIS LINE

        print(f"Found {len(bandit_results)} Bandit, {
              len(gitleaks_results)} Gitleaks, and {len(semgrep_results)} Semgrep issues.")

        # 4. Save Findings & Link to Files
        db_findings_list = []
        for f in all_findings:
            # Check if this file was already added to our map, otherwise create a record for it
            target_file = file_map.get(f.file_path)
            if not target_file and f.file_path:
                target_file = File(
                    repository_id=scan.repository_id,
                    file_path=f.file_path,
                    commit_count=1,
                    author_count=1
                )
                db.add(target_file)
                db.flush()
                file_map[f.file_path] = target_file

            db_finding = Finding(
                scan_id=scan.id,
                file_id=target_file.id if target_file else None,
                scanner_name=f.scanner_name,
                severity=f.severity,
                file_path=f.file_path,
                line_number=f.line_number,
                description=f.description
            )
            db.add(db_finding)
            db_findings_list.append(db_finding)

       # ==========================================
        # 5. CALCULATE REPOSITORY AND FILE RISK
        # ==========================================
        # Repo level risk
        scan.risk_score = calculate_risk_score(db_findings_list)

        # File level risk
        # Group findings by file_id so we can score each file accurately
        for file_path, db_file in file_map.items():
            # Get all findings belonging to this specific file
            file_specific_findings = [
                f for f in db_findings_list if f.file_id == db_file.id]

            # Calculate and assign the score
            db_file.file_risk_score = calculate_file_risk(
                db_file, file_specific_findings)
            db.add(db_file)  # Ensure SQLAlchemy tracks the update

        scan.status = ScanStatus.COMPLETED
        scan.completed_at = datetime.utcnow()
        db.commit()
        print(f"Scan {scan_id} completed. File risk scores calculated.")

    except Exception as e:
        print(f"Scan {scan_id} failed: {e}")
        scan.status = ScanStatus.FAILED
        db.commit()
    finally:
        if os.path.exists(repo_dir):
            # Give Windows a second to release all file locks from subprocesses
            time.sleep(1)

            # Try to delete with a small retry loop
            max_retries = 3
            for i in range(max_retries):
                try:
                    shutil.rmtree(repo_dir, onerror=force_remove_readonly)
                    print(f"Cleaned up temporary directory: {repo_dir}")
                    break
                except Exception as cleanup_error:
                    if i == max_retries - 1:
                        print(f"Warning: Failed to clean up {repo_dir} after {
                              max_retries} attempts. {cleanup_error}")
                    time.sleep(1)  # wait before retrying
