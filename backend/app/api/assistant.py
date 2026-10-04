from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Finding
from app.ai.explainer import generate_finding_explanation

router = APIRouter(prefix="/api/ai", tags=["AI Assistant"])


@router.get("/explain/{finding_id}")
def explain_finding(finding_id: int, db: Session = Depends(get_db)):
    """
    Generates a natural language explanation for a specific vulnerability.
    """
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    explanation = generate_finding_explanation(
        finding_desc=finding.description,
        severity=finding.severity,
        filepath=finding.file_path
    )

    return {
        "finding_id": finding.id,
        "file_path": finding.file_path,
        "ai_explanation": explanation
    }
