from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from backend.database import SessionLocal
from backend import models
from backend.utils.pdf_generator import generate_pdf

router = APIRouter(prefix="/reports", tags=["Reports"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def get_reports(db: Session = Depends(get_db)):
    return db.query(models.Report).all()

@router.post("/")
def create_report(title: str, description: str, db: Session = Depends(get_db)):
    new_report = models.Report(title=title, description=description)
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    return new_report

@router.get("/export-pdf")
def export_pdf(db: Session = Depends(get_db)):
    reports = db.query(models.Report).all()
    if not reports:
        return {"error": "No reports found to export"}
    file_path = generate_pdf(reports)
    return FileResponse(file_path, media_type="application/pdf", filename=file_path.split("/")[-1])
