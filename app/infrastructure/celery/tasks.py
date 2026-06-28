from app.infrastructure.celery.app import celery_app
from app.core.config import settings
from app.core.logging import get_logger
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = get_logger(__name__)


def _build_otp_html(otp: str, app_name: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin:0;padding:0;background-color:#f4f4f4;font-family:Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f4;padding:40px 0;">
            <tr>
                <td align="center">
                    <table width="500" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

                        <!-- Header -->
                        <tr>
                            <td align="center" style="background-color:#4f46e5;padding:32px 40px;">
                                <h1 style="margin:0;color:#ffffff;font-size:24px;font-weight:700;letter-spacing:1px;">
                                    {app_name}
                                </h1>
                            </td>
                        </tr>

                        <!-- Body -->
                        <tr>
                            <td style="padding:40px;">
                                <p style="margin:0 0 16px;color:#374151;font-size:16px;">Hello,</p>
                                <p style="margin:0 0 24px;color:#374151;font-size:16px;line-height:1.6;">
                                    Use the OTP below to complete your verification.
                                    This code is valid for <strong>5 minutes</strong> and can only be used once.
                                </p>

                                <!-- OTP Box -->
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td align="center" style="padding:24px 0;">
                                            <div style="display:inline-block;background-color:#f0f0ff;border:2px dashed #4f46e5;border-radius:8px;padding:16px 48px;">
                                                <span style="font-size:36px;font-weight:700;color:#4f46e5;letter-spacing:12px;">{otp}</span>
                                            </div>
                                        </td>
                                    </tr>
                                </table>

                                <p style="margin:24px 0 0;color:#6b7280;font-size:14px;line-height:1.6;">
                                    If you did not request this, please ignore this email.
                                    Do not share this OTP with anyone.
                                </p>
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="background-color:#f9fafb;padding:20px 40px;border-top:1px solid #e5e7eb;">
                                <p style="margin:0;color:#9ca3af;font-size:12px;text-align:center;">
                                    &copy; {app_name}. All rights reserved.
                                </p>
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


@celery_app.task
def send_otp_email(email: str, otp: str) -> None:
    logger.info("sending_otp_email", email=email)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{settings.app_name} — Your OTP Code"
    msg["From"] = settings.smtp_from
    msg["To"] = email

    # plain text fallback for email clients that don't support HTML
    plain = MIMEText(f"Your OTP is: {otp}. Valid for 5 minutes. Do not share it.", "plain")
    html = MIMEText(_build_otp_html(otp, settings.app_name), "html")

    msg.attach(plain)
    msg.attach(html)   # HTML takes priority, plain is fallback

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        smtp.starttls()
        smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.sendmail(settings.smtp_from, email, msg.as_string())

    logger.info("otp_email_sent", email=email)
