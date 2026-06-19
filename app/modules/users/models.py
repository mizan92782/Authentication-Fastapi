from tortoise import fields
from app.shared.base.base_model import BaseModel
from app.shared.enums.role_enum import RoleEnum


class User(BaseModel):
    first_name = fields.CharField(max_length=30)
    last_name = fields.CharField(max_length=30)
    email = fields.CharField(max_length=200, unique=True)
    hashed_password = fields.CharField(max_length=255)
    is_active = fields.BooleanField(default=True)
    role = fields.CharEnumField(enum_type=RoleEnum, max_length=10, default=RoleEnum.CUSTOMER)
    dp = fields.CharField(max_length=255, null=True)
    
    
    class Meta:
        table = "users"

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'
    
    @property
    def isAdmin(self):
        return self.role == self.isAdmin
        
    @property
    def isActive(self):
        return self.active == True