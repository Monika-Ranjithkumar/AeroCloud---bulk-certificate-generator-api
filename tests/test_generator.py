from pathlib import Path
from PIL import Image
from app.services.generator import CertificateGenerator, generate_certificate_code

def test_certificate_code_generation():
    code1 = generate_certificate_code()
    code2 = generate_certificate_code()
    assert code1.startswith("CERT-")
    assert code2.startswith("CERT-")
    assert code1 != code2

def test_pdf_certificate_generation():
    code = generate_certificate_code()
    pdf_path = CertificateGenerator.generate_pdf(
        certificate_code=code,
        recipient_name="Eleanor Vance",
        course_or_event="Quantum Computing Fundamentals",
        issuer_name="AeroCloud Science Institute",
        issue_date="2026-10-10",
        custom_attributes={"honor": "Summa Cum Laude"}
    )

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0

    # Read binary header to confirm valid PDF output
    with open(pdf_path, "rb") as f:
        header = f.read(5)
        assert header == b"%PDF-"

def test_png_preview_generation():
    code = generate_certificate_code()
    preview_path = CertificateGenerator.generate_preview(
        certificate_code=code,
        recipient_name="Eleanor Vance",
        course_or_event="Quantum Computing Fundamentals",
        issuer_name="AeroCloud Science Institute",
        issue_date="2026-10-10"
    )

    assert preview_path.exists()
    assert preview_path.stat().st_size > 0

    # Verify PIL image can load preview PNG
    with Image.open(preview_path) as img:
        assert img.format == "PNG"
        assert img.width == 1100
        assert img.height == 850
