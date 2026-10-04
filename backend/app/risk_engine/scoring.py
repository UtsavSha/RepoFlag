from typing import List
from app.models import Finding

# Heuristic weights for different severity levels
SEVERITY_WEIGHTS = {
    "CRITICAL": 10.0,
    "HIGH": 5.0,
    "MEDIUM": 2.0,
    "LOW": 0.5,
    "UNKNOWN": 0.1
}


def calculate_risk_score(findings: List[Finding]) -> float:
    """
    Calculates a repository risk score based on the severity of its findings.
    Returns a float between 0.0 (No Risk) and 100.0 (Maximum Risk).
    """
    if not findings:
        return 0.0

    raw_score = 0.0

    for finding in findings:
        # Get the weight, default to UNKNOWN if the scanner output is weird
        weight = SEVERITY_WEIGHTS.get(
            finding.severity.upper(), SEVERITY_WEIGHTS["UNKNOWN"])
        raw_score += weight

    # Cap the score at 100.0 to keep it within a standard percentage gauge
    final_score = min(100.0, raw_score)

    # Round to 2 decimal places for a clean UI presentation
    return round(final_score, 2)
