from app.modules.auth.service import AuthService
from fastapi import APIRouter, Form, Request, HTTPException
from app.modules.auth.schemas import OtpVeritySchema, UserRegisterSchema
from app.shared.throttling.ip import get_ip
from app.shared.throttling.ratelimiting import non_user_allowed

router = APIRouter()


@router.post("/user/register/", summary="Register a new user")
async def register_user(
    request: Request,
    first_name: str = Form(..., description="e.g. John"),
    last_name: str = Form(..., description="e.g. Doe"),
    email: str = Form(..., description="Must end with @gmail.com"),
    password1: str = Form(..., description="Exactly 8 characters"),
    password2: str = Form(..., description="Must match password1"),
):
    user = UserRegisterSchema(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password1=password1,
        password2=password2
    )
    
    ip = get_ip(request)
    if not await non_user_allowed(ip):
        raise HTTPException(429, "Too many requests")
    
    return await AuthService.registration_otp_cache(user)
    
    
    
@router.post("/user/register/otp-verify/", summary="Verify Otp for email registration")
async def register_opt_verify(
    request: Request,
    email: str = Form(..., description="Enter email to verify otp"),
    otp: str = Form(..., description="Enter otp to verify account creation"),
):
    verification = OtpVeritySchema(
        email=email,
        otp=otp
    )
    return await AuthService.registration_otp_verification(verification)