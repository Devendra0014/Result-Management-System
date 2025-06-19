from xhtml2pdf import pisa
from flask import render_template
import os

def render_pdf(template_name, context, output_filename):
    html = render_template(template_name, **context)
    pdf_path = os.path.join("static", "pdf", output_filename)
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

    with open(pdf_path, "w+b") as pdf_file:
        pisa_status = pisa.CreatePDF(html, dest=pdf_file)
        return pdf_path if not pisa_status.err else None
