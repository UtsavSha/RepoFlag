import subprocess
import json
from typing import List
from app.scanners.normalizer import NormalizedFinding


def run_trivy(repo_path: str) -> List[NormalizedFinding]:
    """Runs Trivy Software Composition Analysis (SCA) for vulnerable dependencies."""
    print(f"Running Trivy on {repo_path}...")

    # We only scan 'vuln' (vulnerabilities) to keep it fast
    cmd = [
        "trivy", "fs",
        "--format", "json",
        "--quiet",
        "--scanners", "vuln",
        repo_path
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False)

        if not result.stdout:
            return []

        raw_output = json.loads(result.stdout)
        normalized_findings = []

        # Trivy groups results by the target file (e.g., package.json)
        for result_group in raw_output.get("Results", []):
            target_file = result_group.get("Target", "").replace(
                repo_path, "").lstrip("/\\")

            for vuln in result_group.get("Vulnerabilities", []):
                severity = vuln.get("Severity", "MEDIUM").upper()
                if severity not in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]:
                    severity = "UNKNOWN"

                pkg_name = vuln.get("PkgName", "Unknown Package")
                installed_ver = vuln.get("InstalledVersion", "")
                fixed_ver = vuln.get("FixedVersion", "No fix available")
                vuln_id = vuln.get("VulnerabilityID", "CVE-UNKNOWN")

                desc = f"[{vuln_id}] {pkg_name} ({installed_ver}): {vuln.get(
                    'Title', 'Vulnerability detected')}. Fix: {fixed_ver}"

                finding = NormalizedFinding(
                    scanner_name="trivy",
                    severity=severity,
                    file_path=target_file,
                    line_number=None,
                    description=desc[:1000],
                    raw_data=vuln
                )
                normalized_findings.append(finding)

        return normalized_findings

    except FileNotFoundError:
        print("ERROR: 'trivy' command not found. Install it via: winget install AquaSecurity.Trivy")
        return []
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse Trivy JSON output: {str(e)}")
        return []
    except Exception as e:
        print(f"Unexpected error running Trivy: {str(e)}")
        return []
