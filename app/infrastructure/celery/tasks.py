from app.infrastructure.celery.app import celery_app
from app.core.config import settings
from app.core.logging import get_logger
import smtplib
from email.mime.text import MIMEText

logger = get_logger(__name__)


@celery_app.task
def registraion_otp_send_eamil_delay(email, otp):
    logger.info("sending_registration_otp", email=email)
    msg = MIMEText(f"Your OTP is: {otp}. Valid for 5 minutes.")
    msg["Subject"] = "Registration OTP"
    msg["From"] = settings.smtp_from
    msg["To"] = email
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        smtp.starttls()
        smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.sendmail(settings.smtp_from, email, msg.as_string())
    logger.info("registration_otp_sent", email=email)