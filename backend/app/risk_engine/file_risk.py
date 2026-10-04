from typing import List
from app.models import Finding, File

# Same weights as repository scoring
SEVERITY_WEIGHTS = {
    "CRITICAL": 10.0,
    "HIGH": 5.0,
    "MEDIUM": 2.0,
    "LOW": 0.5,
    "UNKNOWN": 0.1
}


def calculate_file_risk(file_obj: File, findings: List[Finding]) -> float:
    # 1. Static score from vulnerabilities
    static_score = sum([SEVERITY_WEIGHTS.get(
        f.severity.upper(), 0.1) for f in findings])

    # 2. Dynamic multipliers
    commit_factor = min(file_obj.commit_count * 0.05, 1.5)
    author_factor = min(file_obj.author_count * 0.1, 1.0)

    # ADD COMPLEXITY FACTOR: Anything above 10 is considered highly complex
    complexity_factor = 0.0
    if file_obj.complexity_score > 10.0:
        complexity_factor = min((file_obj.complexity_score - 10.0) * 0.1, 2.0)

    # Base multiplier is 1.0
    churn_multiplier = 1.0 + commit_factor + author_factor + complexity_factor

    # 3. Final Calculation
    raw_score = static_score * churn_multiplier

    # Even if there are NO static findings (0 static score), a highly complex
    # file that changes constantly still carries inherent risk.
    if raw_score == 0 and churn_multiplier > 1.5:
        raw_score = churn_multiplier * 2.0

    return round(min(100.0, raw_score), 2)
