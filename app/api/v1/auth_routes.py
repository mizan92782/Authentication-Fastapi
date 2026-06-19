from fastapi import APIRouter, Form
from app.modules.auth.schemas import UserRegisterSchema

router = APIRouter()


@router.post("/user/register/", summary="Register a new user")
def register_user(
    first_name: str = Form(..., description="e.g. John"),
    last_name: str = Form(..., description="e.g. Doe"),
    email: str = Form(..., description="Must end with @gmail.com"),
    password1: str = Form(..., description="Exactly 8 characters"),
    password2: str = Form(..., description="Must match password1"),
):
    """
    Register a new user account.

    - **email**: must end with `@gmail.com`
    - **password1 / password2**: must match, exactly 8 characters
    - **djfkdfdkfjdkfj**
    """
    user = UserRegisterSchema(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password1=password1,
        password2=password2
    )

    return {
        "message": "User registered successfully",
        "data": user.model_dump()
    }
    