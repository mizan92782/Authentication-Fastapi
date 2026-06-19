import secrets

class OTPService:

    @staticmethod
    def otp_generator(length=4):
        otp = ''.join(str(secrets.randbelow(10)) for _ in range(length))
        return otp