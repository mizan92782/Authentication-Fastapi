from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from app.shared.enums.role_enum import RoleEnum


class UserRegisterSchema(BaseModel):

    first_name: str
    last_name: str
    email: EmailStr

    password1: str = Field(min_length=8, max_length=8)
    password2: str = Field(min_length=8, max_length=8)

    @field_validator("first_name", "last_name")
    @classmethod
    def name_must_not_be_empty(cls, v):
        if not v or v.strip() == "":
            raise ValueError("Name cannot be empty")
        return v

    @field_validator("email")
    @classmethod
    def email_must_not_be_empty(cls, v):
        if not v or v.strip() == "" or not v.endswith("@gmail.com"):
            raise ValueError("Email cannot be empty or must end with @gmail.com")
        return v

    @field_validator("password1", "password2")
    @classmethod
    def password_must_not_be_empty(cls, v):
        if not v or v.strip() == "":
            raise ValueError("Password cannot be empty")
        return v

    @model_validator(mode="after")
    def check_password_match(self):
        if self.password1 != self.password2:
            raise ValueError("Passwords do not match")
        return self