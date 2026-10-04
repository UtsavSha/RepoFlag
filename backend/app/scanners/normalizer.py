from pydantic import BaseModel
from typing import Optional, Dict, Any


class NormalizedFinding(BaseModel):
    scanner_name: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    file_path: str
    line_number: Optional[int]
    description: str
    # Stores the original JSON for the AI Explainer later
    raw_data: Dict[str, Any]
