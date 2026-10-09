import io
import os
import uuid
import qrcode
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas

from app.config import settings

def generate_certificate_code() -> str:
    """Generate a unique printable certificate code like CERT-2026-X89A2B."""
    random_part = uuid.uuid4().hex[:8].upper()
    year = datetime.now().year
    return f"CERT-{year}-{random_part}"

TEMPLATES = {
    "classic_gold": {
        "primary": "#1E3A8A",      # Navy Blue
        "secondary": "#D97706",    # Gold
        "text_dark": "#0F172A",    # Dark Slate
        "text_muted": "#475569",   # Muted Slate
        "line_color": "#CBD5E1",   # Light Gray
        "bg_color": "#F8FAFC"
    },
    "modern_emerald": {
        "primary": "#065F46",      # Deep Emerald Green
        "secondary": "#10B981",    # Bright Mint
        "text_dark": "#022C22",    # Dark Emerald
        "text_muted": "#047857",   # Medium Emerald
        "line_color": "#A7F3D0",   # Soft Mint Line
        "bg_color": "#F0FDF4"
    },
    "executive_crimson": {
        "primary": "#881337",      # Burgundy Crimson
        "secondary": "#D97706",    # Regal Gold
        "text_dark": "#4C0519",    # Dark Red
        "text_muted": "#9F1239",   # Medium Rose
        "line_color": "#FECDD3",   # Soft Pink Line
        "bg_color": "#FFF1F2"
    },
    "minimalist_purple": {
        "primary": "#4C1D95",      # Deep Indigo / Purple
        "secondary": "#8B5CF6",    # Vibrant Violet
        "text_dark": "#1E1B4B",    # Dark Indigo
        "text_muted": "#6D28D9",   # Medium Violet
        "line_color": "#DDD6FE",   # Soft Lavender Line
        "bg_color": "#F5F3FF"
    }
}

class CertificateGenerator:
    """Engine to build high quality PDF certificates and PNG preview images with customizable themes."""

    @classmethod
    def get_template_style(cls, template_id: str) -> dict:
        return TEMPLATES.get(template_id, TEMPLATES["classic_gold"])

    @classmethod
    def generate_pdf(
        cls,
        certificate_code: str,
        recipient_name: str,
        course_or_event: str,
        issuer_name: str,
        issue_date: str,
        custom_attributes: dict = None,
        template_id: str = "classic_gold"
    ) -> Path:
        output_path = settings.CERTIFICATES_DIR / f"{certificate_code}.pdf"
        style = cls.get_template_style(template_id)
        
        # Dimensions for Landscape Letter (11 x 8.5 inches = 792 x 612 points)
        width, height = landscape(letter)

        # Generate QR code image
        verification_url = f"{settings.BASE_VERIFICATION_URL}/{certificate_code}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=4,
            border=2,
        )
        qr.add_data(verification_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)
        
        # Save temporary QR image file for ReportLab
        temp_qr_path = settings.STORAGE_DIR / f"temp_qr_{certificate_code}.png"
        with open(temp_qr_path, "wb") as f:
            f.write(qr_buffer.getvalue())

        c = canvas.Canvas(str(output_path), pagesize=landscape(letter))

        # --- Background & Double Border ---
        # Outer Border
        c.setStrokeColor(colors.HexColor(style["primary"]))
        c.setLineWidth(5)
        c.rect(20, 20, width - 40, height - 40)

        # Inner Decorative Border
        c.setStrokeColor(colors.HexColor(style["secondary"]))
        c.setLineWidth(2)
        c.rect(28, 28, width - 56, height - 56)

        # Corner Accents
        c.setFillColor(colors.HexColor(style["primary"]))
        c.rect(20, 20, 15, 15, fill=1, stroke=0)
        c.rect(width - 35, 20, 15, 15, fill=1, stroke=0)
        c.rect(20, height - 35, 15, 15, fill=1, stroke=0)
        c.rect(width - 35, height - 35, 15, 15, fill=1, stroke=0)

        # --- Header Elements ---
        c.setFillColor(colors.HexColor(style["primary"]))
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(width / 2.0, height - 80, issuer_name.upper())

        c.setFillColor(colors.HexColor(style["text_dark"]))
        c.setFont("Helvetica-Bold", 32)
        c.drawCentredString(width / 2.0, height - 135, "CERTIFICATE OF ACHIEVEMENT")

        # Decorative line below header
        c.setStrokeColor(colors.HexColor(style["secondary"]))
        c.setLineWidth(1.5)
        c.line(width / 2.0 - 150, height - 150, width / 2.0 + 150, height - 150)

        # Subtitle
        c.setFillColor(colors.HexColor(style["text_muted"]))
        c.setFont("Helvetica-Oblique", 14)
        c.drawCentredString(width / 2.0, height - 190, "PROUDLY PRESENTED TO")

        # --- Recipient Name ---
        c.setFillColor(colors.HexColor(style["primary"]))
        c.setFont("Helvetica-Bold", 30)
        c.drawCentredString(width / 2.0, height - 250, recipient_name)

        # Line under name
        c.setStrokeColor(colors.HexColor(style["line_color"]))
        c.setLineWidth(1)
        c.line(width / 2.0 - 200, height - 265, width / 2.0 + 200, height - 265)

        # --- Course / Event Description ---
        c.setFillColor(colors.HexColor(style["text_muted"]))
        c.setFont("Helvetica", 14)
        c.drawCentredString(
            width / 2.0,
            height - 310,
            "for successfully completing and demonstrating excellence in"
        )

        c.setFillColor(colors.HexColor(style["text_dark"]))
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(width / 2.0, height - 350, course_or_event)

        # Custom Attributes (if provided)
        if custom_attributes and isinstance(custom_attributes, dict):
            attr_str = " | ".join([f"{k.capitalize()}: {v}" for k, v in custom_attributes.items() if isinstance(v, (str, int, float))])
            if attr_str:
                c.setFillColor(colors.HexColor(style["text_muted"]))
                c.setFont("Helvetica-Oblique", 11)
                c.drawCentredString(width / 2.0, height - 380, attr_str)

        # --- Footer Elements: Date, Signature, Verification & QR Code ---
        # Date (Left bottom)
        c.setFillColor(colors.HexColor(style["text_dark"]))
        c.setFont("Helvetica-Bold", 12)
        c.drawString(70, 110, issue_date)
        c.setStrokeColor(colors.HexColor(style["line_color"]))
        c.line(65, 100, 200, 100)
        c.setFillColor(colors.HexColor(style["text_muted"]))
        c.setFont("Helvetica", 10)
        c.drawString(70, 85, "Date of Issuance")

        # Authorized Signature (Center bottom)
        c.setFillColor(colors.HexColor(style["primary"]))
        c.setFont("Helvetica-BoldOblique", 16)
        c.drawCentredString(width / 2.0, 110, issuer_name)
        c.setStrokeColor(colors.HexColor(style["line_color"]))
        c.line(width / 2.0 - 90, 100, width / 2.0 + 90, 100)
        c.setFillColor(colors.HexColor(style["text_muted"]))
        c.setFont("Helvetica", 10)
        c.drawCentredString(width / 2.0, 85, "Authorized Representative")

        # Draw QR Code (Right bottom)
        c.drawImage(str(temp_qr_path), width - 150, 60, width=80, height=80)
        c.setFillColor(colors.HexColor(style["text_muted"]))
        c.setFont("Helvetica", 8)
        c.drawRightString(width - 65, 48, f"ID: {certificate_code}")

        c.save()

        # Cleanup temporary QR code file
        if os.path.exists(temp_qr_path):
            try:
                os.remove(temp_qr_path)
            except Exception:
                pass

        return output_path

    @classmethod
    def generate_preview(
        cls,
        certificate_code: str,
        recipient_name: str,
        course_or_event: str,
        issuer_name: str,
        issue_date: str,
        template_id: str = "classic_gold"
    ) -> Path:
        """Generate high resolution PNG image preview using PIL."""
        preview_path = settings.PREVIEWS_DIR / f"{certificate_code}.png"
        style = cls.get_template_style(template_id)
        
        # Image dimensions: 1100 x 850 px
        width, height = 1100, 850
        img = Image.new("RGB", (width, height), color=style["bg_color"])
        draw = ImageDraw.Draw(img)

        # Outer & Inner borders
        draw.rectangle([20, 20, width - 20, height - 20], outline=style["primary"], width=8)
        draw.rectangle([32, 32, width - 32, height - 32], outline=style["secondary"], width=3)

        # Default fallback font handling
        try:
            font_title = ImageFont.truetype("arial.ttf", 38)
            font_sub = ImageFont.truetype("arial.ttf", 20)
            font_name = ImageFont.truetype("arial.ttf", 42)
            font_body = ImageFont.truetype("arial.ttf", 22)
            font_small = ImageFont.truetype("arial.ttf", 14)
        except Exception:
            font_title = font_sub = font_name = font_body = font_small = ImageFont.load_default()

        # Draw text elements
        draw.text((width / 2, 90), issuer_name.upper(), fill=style["primary"], font=font_sub, anchor="mm")
        draw.text((width / 2, 160), "CERTIFICATE OF ACHIEVEMENT", fill=style["text_dark"], font=font_title, anchor="mm")
        draw.line([(width / 2 - 200, 200), (width / 2 + 200, 200)], fill=style["secondary"], width=3)

        draw.text((width / 2, 250), "PROUDLY PRESENTED TO", fill=style["text_muted"], font=font_sub, anchor="mm")
        draw.text((width / 2, 340), recipient_name, fill=style["primary"], font=font_name, anchor="mm")
        draw.line([(width / 2 - 250, 380), (width / 2 + 250, 380)], fill=style["line_color"], width=2)

        draw.text((width / 2, 450), "for successfully completing the course:", fill=style["text_muted"], font=font_sub, anchor="mm")
        draw.text((width / 2, 510), course_or_event, fill=style["text_dark"], font=font_body, anchor="mm")

        # Footer Date & Signature
        draw.text((120, 680), f"Date: {issue_date}", fill=style["text_dark"], font=font_sub)
        draw.line([(120, 710), (320, 710)], fill=style["line_color"], width=2)
        draw.text((120, 720), "Date of Issuance", fill=style["text_muted"], font=font_small)

        draw.text((width / 2, 680), issuer_name, fill=style["primary"], font=font_sub, anchor="mm")
        draw.line([(width / 2 - 120, 710), (width / 2 + 120, 710)], fill=style["line_color"], width=2)
        draw.text((width / 2, 720), "Authorized Representative", fill=style["text_muted"], font=font_small, anchor="mm")

        # Draw QR Code on Preview
        verification_url = f"{settings.BASE_VERIFICATION_URL}/{certificate_code}"
        qr = qrcode.QRCode(box_size=3, border=1)
        qr.add_data(verification_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        
        img.paste(qr_img, (width - 220, 640))
        draw.text((width - 120, 755), f"ID: {certificate_code}", fill=style["text_muted"], font=font_small, anchor="mm")

        img.save(preview_path)
        return preview_path
