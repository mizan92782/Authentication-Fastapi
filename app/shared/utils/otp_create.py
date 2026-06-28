import secrets


class OTPService:

    @staticmethod
    def otp_generator(length: int = 6) -> str:
        return "".join(str(secrets.randbelow(10)) for _ in range(length))
