import subprocess
import json
from typing import List
from app.scanners.normalizer import NormalizedFinding


def run_bandit(repo_path: str) -> List[NormalizedFinding]:
    """
    Runs the Bandit security scanner against a repository and normalizes the output.
    """
    print(f"Running Bandit on {repo_path}...")

    # -r for recursive, -f json for JSON output
    cmd = [
        "bandit",
        "-r", repo_path,
        "-f", "json"
    ]

    try:
        # Bandit returns exit code 1 if it finds vulnerabilities.
        # We set check=False so it doesn't raise an exception on exit code 1.
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )

        # Exit code 2+ indicates a crash or syntax error, not just vulnerabilities
        if result.returncode > 1:
            print(f"Bandit execution error: {result.stderr}")
            return []

        if not result.stdout:
            return []

        raw_output = json.loads(result.stdout)
        normalized_findings = []

        for issue in raw_output.get("results", []):
            severity = issue.get("issue_severity", "LOW").upper()

            # Clean up the file path to be relative to the repo root
            # instead of showing the messy temporary Windows path
            file_path = issue.get("filename", "").replace(
                repo_path, "").lstrip("/\\")

            finding = NormalizedFinding(
                scanner_name="bandit",
                severity=severity,
                file_path=file_path,
                line_number=issue.get("line_number"),
                description=f"[{issue.get('test_id')}] {
                    issue.get('issue_text')}",
                raw_data=issue
            )
            normalized_findings.append(finding)

        return normalized_findings

    except FileNotFoundError:
        print("ERROR: 'bandit' command not found. Ensure it is installed via pip.")
        return []
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse Bandit JSON output: {str(e)}")
        return []
    except Exception as e:
        print(f"Unexpected error running Bandit: {str(e)}")
        return []
