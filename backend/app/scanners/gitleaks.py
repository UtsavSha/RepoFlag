import subprocess
import json
import os
import tempfile
from typing import List
from app.scanners.normalizer import NormalizedFinding


def run_gitleaks(repo_path: str) -> List[NormalizedFinding]:
    """Runs Gitleaks to detect hardcoded secrets and API keys."""
    print(f"Running Gitleaks on {repo_path}...")

    # Create a temporary file to store the Gitleaks JSON output safely
    fd, temp_report = tempfile.mkstemp(suffix=".json")
    os.close(fd)

    # --no-git tells Gitleaks to scan the directory as plain files,
    # which is faster for a single-point-in-time scan.
    cmd = [
        "gitleaks", "detect",
        "--source", repo_path,
        "--report-path", temp_report,
        "--report-format", "json",
        "--no-git"
    ]

    try:
        # Gitleaks returns 1 if leaks are present, 0 if clean.
        subprocess.run(cmd, capture_output=True, text=True, check=False)

        if not os.path.exists(temp_report) or os.path.getsize(temp_report) == 0:
            return []

        with open(temp_report, 'r', encoding='utf-8') as f:
            raw_output = json.load(f)

        findings = []
        for issue in raw_output:
            finding = NormalizedFinding(
                scanner_name="gitleaks",
                severity="CRITICAL",  # Secrets are always critical
                file_path=issue.get("File", "").replace(
                    repo_path, "").lstrip("/\\"),
                line_number=issue.get("StartLine"),
                description=f"[{issue.get('RuleID')}] Exposed Secret: {
                    issue.get('Description')}",
                raw_data=issue
            )
            findings.append(finding)

        return findings

    except Exception as e:
        print(f"Error running Gitleaks: {e}")
        return []
    finally:
        if os.path.exists(temp_report):
            os.remove(temp_report)
