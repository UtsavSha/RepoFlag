import subprocess
import json
import os
from typing import List
from app.scanners.normalizer import NormalizedFinding


def run_semgrep(repo_path: str) -> List[NormalizedFinding]:
    """Runs Semgrep for multi-language static analysis."""
    print(f"Running Semgrep on {repo_path}...")

    # --config auto detects the language and runs standard security rules
    # --json outputs machine-readable results
    cmd = [
        "semgrep", "scan",
        "--config", "auto",
        "--json",
        "--quiet",
        repo_path
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False)

        if not result.stdout:
            return []

        raw_output = json.loads(result.stdout)
        normalized_findings = []

        for issue in raw_output.get("results", []):
            # Semgrep uses 'ERROR', 'WARNING', 'INFO'. We map this to our Severities.
            semgrep_severity = issue.get("extra", {}).get(
                "severity", "WARNING").upper()
            severity_map = {
                "ERROR": "CRITICAL",
                "WARNING": "MEDIUM",
                "INFO": "LOW"
            }
            severity = severity_map.get(semgrep_severity, "MEDIUM")

            finding = NormalizedFinding(
                scanner_name="semgrep",
                severity=severity,
                file_path=issue.get("path", "").replace(
                    repo_path, "").lstrip("/\\"),
                line_number=issue.get("start", {}).get("line"),
                description=f"[{issue.get('check_id')}] {issue.get(
                    'extra', {}).get('message', 'Issue detected')}",
                raw_data=issue
            )
            normalized_findings.append(finding)

        return normalized_findings

    except FileNotFoundError:
        print("ERROR: 'semgrep' command not found. Ensure it is installed via pip.")
        return []
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse Semgrep JSON output: {str(e)}")
        return []
    except Exception as e:
        print(f"Unexpected error running Semgrep: {str(e)}")
        return []
