from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Repository, Scan, ScanStatus, Finding
from app.services.scan_service import execute_scan_pipeline  # Import the new service
from app.models import File
from fastapi.responses import FileResponse
from app.reports.pdf_generator import generate_scan_pdf

router = APIRouter(prefix="/api/scans", tags=["Scans"])


@router.post("/{repository_id}")
def trigger_scan(repository_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repository_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    scan = Scan(repository_id=repo.id, status=ScanStatus.PENDING)
    db.add(scan)
    db.commit()
    db.refresh(scan)

    # Call the actual Git clone pipeline
    background_tasks.add_task(execute_scan_pipeline, scan.id, repo.url, db)

    return {"message": "Scan triggered successfully", "scan_id": scan.id}


@router.get("/{scan_id}")
def get_scan_status(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return {"scan_id": scan.id, "status": scan.status}


@router.get("/{scan_id}/details")
def get_scan_details(scan_id: int, db: Session = Depends(get_db)):
    """
    Fetches the full scan object along with its findings.
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    return {
        "id": scan.id,
        "repository_id": scan.repository_id,
        "status": scan.status,
        "started_at": scan.started_at,
        "completed_at": scan.completed_at,
        "risk_score": scan.risk_score,
        "finding_count": db.query(Finding).filter(Finding.scan_id == scan_id).count()
    }


@router.get("/{scan_id}/findings")
def get_scan_findings(
    scan_id: int,
    severity: str = None,
    db: Session = Depends(get_db)
):
    """
    Fetches the vulnerabilities found in a specific scan.
    Optionally filter by severity (e.g., ?severity=HIGH).
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    query = db.query(Finding).filter(Finding.scan_id == scan_id)

    if severity:
        query = query.filter(Finding.severity == severity.upper())

    findings = query.all()

    return [
        {
            "id": f.id,
            "scanner_name": f.scanner_name,
            "severity": f.severity,
            "file_path": f.file_path,
            "line_number": f.line_number,
            "description": f.description
        } for f in findings
    ]


@router.get("/{scan_id}/heatmap")
def get_risk_heatmap(scan_id: int, db: Session = Depends(get_db)):
    """
    Returns files sorted by their calculated risk score to generate the UI Heatmap.
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    # Query files associated with this repository, ordered by risk score descending
    files = db.query(File)\
              .filter(File.repository_id == scan.repository_id)\
              .order_by(File.file_risk_score.desc())\
              .limit(50)\
              .all()

    return [
        {
            "file_path": f.file_path,
            "risk_score": f.file_risk_score,
            "commits": f.commit_count,
            "authors": f.author_count,
            # Count findings associated with this specific file and scan
            "finding_count": db.query(Finding).filter(Finding.file_id == f.id, Finding.scan_id == scan_id).count()
        } for f in files
    ]


@router.get("/{scan_id}/report/download")
def download_scan_report(scan_id: int, db: Session = Depends(get_db)):
    """
    Generates and downloads a PDF security report for the scan.
    """
    try:
        pdf_path = generate_scan_pdf(scan_id, db)

        # FileResponse automatically handles downloading the file to the user's browser
        return FileResponse(
            path=pdf_path,
            filename=f"REPOFLAG_Security_Report_{scan_id}.pdf",
            media_type="application/pdf"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate PDF: {str(e)}")
