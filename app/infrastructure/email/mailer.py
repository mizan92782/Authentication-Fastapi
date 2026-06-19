"""Email sending utilities."""

from app.infrastructure.celery.tasks import registraion_otp_send_eamil_delay


class EmailServices:

    @staticmethod
    def registration_otp_send_email(email,otp):
        registraion_otp_send_eamil_delay.delay(email,otp)

        