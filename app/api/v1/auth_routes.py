from app.modules.auth.service import AuthService
from fastapi import APIRouter, Form
from app.modules.auth.schemas import UserRegisterSchema

router = APIRouter()


@router.post("/user/register/", summary="Register a new user")
async def register_user(
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
    return await AuthService.registration_otp_cache(user)