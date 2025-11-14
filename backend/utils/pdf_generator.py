import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime

def generate_pdf(reports, output_dir="reports_pdfs"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    filename = f"ReportSummary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(file_path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>Offline Report Summary</b>", styles["Title"]))
    elements.append(Spacer(1, 20))

    for r in reports:
        elements.append(Paragraph(f"<b>Title:</b> {r.title}", styles["Heading3"]))
        elements.append(Paragraph(f"{r.description}", styles["Normal"]))
        elements.append(Spacer(1, 15))

    doc.build(elements)
    return file_path
