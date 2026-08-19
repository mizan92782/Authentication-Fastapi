from app.mcp.http import post_form, post_json


def register_auth_tools(mcp):

    @mcp.tool()
    async def auth_register(first_name: str, last_name: str, email: str, password: str, confirm_password: str) -> dict:
        """Register a new user. Sends a 6-digit OTP to the email. OTP expires in 5 minutes."""
        return await post_form("/api/v1/auth/user/register/", {
            "first_name": first_name, "last_name": last_name,
            "email": email, "password": password, "confirm_password": confirm_password,
        })

    @mcp.tool()
    async def auth_verify_otp(email: str, otp: str) -> dict:
        """Verify registration OTP. On success returns access_token and refresh_token."""
        return await post_form("/api/v1/auth/user/otp-verify/", {"email": email, "otp": otp})

    @mcp.tool()
    async def auth_resend_otp(email: str) -> dict:
        """Resend registration OTP (60 second cooldown between resends)."""
        return await post_form("/api/v1/auth/user/otp-resend/", {"email": email})

    @mcp.tool()
    async def auth_login(email: str, password: str) -> dict:
        """Login with email and password. Returns access_token and refresh_token."""
        return await post_json("/api/v1/auth/user/login/", {"email": email, "password": password})

    @mcp.tool()
    async def auth_refresh_token(refresh_token: str) -> dict:
        """Exchange a refresh token for a new access token."""
        return await post_form("/api/v1/auth/user/token-refresh/", {"refresh_token": refresh_token})

    @mcp.tool()
    async def auth_logout(refresh_token: str) -> dict:
        """Logout — blacklists the refresh token so it cannot be reused."""
        return await post_form("/api/v1/auth/user/logout/", {"refresh_token": refresh_token})

    @mcp.tool()
    async def auth_password_reset(email: str) -> dict:
        """Request a password reset OTP. Always returns the same message to prevent email enumeration."""
        return await post_form("/api/v1/auth/user/password-reset/", {"email": email})

    @mcp.tool()
    async def auth_password_change(email: str, otp: str, new_password: str, confirm_password: str) -> dict:
        """Change password using OTP received via email. Locked after 3 failed attempts."""
        return await post_form("/api/v1/auth/user/password-change/", {
            "email": email, "otp": otp,
            "new_password": new_password, "confirm_password": confirm_password,
        })
