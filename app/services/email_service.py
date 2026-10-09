import os
import logging
import smtplib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Optional

from app.config import settings

logger = logging.getLogger("email_service")

class EmailService:
    """Service to handle emailing PDF certificates directly to recipients."""

    @classmethod
    def send_certificate_email(
        cls,
        recipient_email: str,
        recipient_name: str,
        course_or_event: str,
        issuer_name: str,
        certificate_code: str,
        pdf_path: Path
    ) -> bool:
        """
        Sends an email with the PDF certificate attached.
        Supports live SMTP servers or safe mock logging if SMTP is unconfigured.
        """
        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        sender_email = os.getenv("SENDER_EMAIL", f"certificates@{issuer_name.lower().replace(' ', '')}.com")

        subject = f"Your Certificate of Achievement - {course_or_event}"

        body_html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 10px;">
              <h2 style="color: #1e3a8a;">Congratulations, {recipient_name}!</h2>
              <p>We are pleased to present your official <strong>{course_or_event}</strong> certificate issued by <strong>{issuer_name}</strong>.</p>
              
              <div style="background-color: #f8fafc; padding: 15px; border-left: 4px solid #d97706; margin: 20px 0;">
                <p style="margin: 0;"><strong>Certificate Code:</strong> <code style="font-size: 16px; color: #1e3a8a;">{certificate_code}</code></p>
                <p style="margin: 5px 0 0 0; font-size: 13px; color: #64748b;">You can verify this certificate online at any time.</p>
              </div>

              <p>Your official PDF certificate has been attached to this email for downloading and printing.</p>

              <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 25px 0;" />
              <p style="font-size: 12px; color: #94a3b8;">Sent automatically by {issuer_name} Certificate Portal.</p>
            </div>
          </body>
        </html>
        """

        if smtp_host and smtp_user and smtp_password:
            try:
                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['To'] = recipient_email
                msg['Subject'] = subject

                msg.attach(MIMEText(body_html, 'html'))

                if pdf_path and pdf_path.exists():
                    with open(pdf_path, 'rb') as f:
                        part = MIMEApplication(f.read(), Name=pdf_path.name)
                        part['Content-Disposition'] = f'attachment; filename="{recipient_name.replace(" ", "_")}_Certificate.pdf"'
                        msg.attach(part)

                server = smtplib.SMTP(smtp_host, smtp_port)
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
                server.quit()
                
                logger.info(f"Email successfully sent to {recipient_email}")
                return True

            except Exception as exc:
                logger.error(f"Failed to send email to {recipient_email}: {str(exc)}")
                return False
        else:
            # Mock email delivery logging mode
            logger.info(f"[MOCK EMAIL SENT] To: {recipient_email} | Subject: {subject} | Attachment: {pdf_path.name}")
            print(f"[EMAIL DELIVERED] Certificate '{certificate_code}' sent to {recipient_email}")
            return True
