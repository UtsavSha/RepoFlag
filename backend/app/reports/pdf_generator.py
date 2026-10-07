import os
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from sqlalchemy.orm import Session

from app.models import Scan, Repository, Finding


def generate_scan_pdf(scan_id: int, db: Session) -> str:
    """Generates a PDF report for a given scan and returns the file path."""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise ValueError("Scan not found")

    repo = db.query(Repository).filter(
        Repository.id == scan.repository_id).first()
    findings = db.query(Finding).filter(Finding.scan_id ==
                                        scan_id).order_by(Finding.severity).all()

    # 1. Setup Jinja2 template environment
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(base_dir, 'templates')

    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('report.html')

    # 2. Render the HTML string with actual data
    scan_date = scan.completed_at.strftime(
        "%Y-%m-%d %H:%M") if scan.completed_at else "Incomplete"

    html_out = template.render(
        repo_name=repo.name,
        repo_url=repo.url,
        scan_date=scan_date,
        risk_score=scan.risk_score,
        total_findings=len(findings),
        findings=findings
    )

    # 3. Create an exports directory
    export_dir = os.path.join(base_dir, '..', 'exports')
    os.makedirs(export_dir, exist_ok=True)

    output_pdf_path = os.path.join(
        export_dir, f"repoflag_report_{scan_id}.pdf")

    # 4. Convert HTML to PDF using xhtml2pdf
    with open(output_pdf_path, "w+b") as result_file:
        pisa_status = pisa.CreatePDF(
            src=html_out,
            dest=result_file
        )

    # pisa_status.err is True if there was an error
    if pisa_status.err:
        raise Exception("Failed to generate PDF document.")

    return output_pdf_path
