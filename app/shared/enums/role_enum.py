from enum import Enum


class RoleEnum(str, Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"