from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class Users(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: str
    last_name : str
    status: bool = True
    role_id: int

class Login(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserProfileUpdate(BaseModel):
    """Autoedición de perfil: el propio usuario NO puede cambiar su email
    por este medio (ver UserAdminUpdate para la excepción de administrador)."""
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserAdminUpdate(BaseModel):
    """Edición de datos de un usuario por un administrador (permiso
    'users:update'). A diferencia de UserProfileUpdate, sí permite email,
    y además deja reasignar el rol y activar/desactivar la cuenta."""
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role_id: Optional[int] = None
    status: Optional[bool] = None

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=72)

class AvatarOut(BaseModel):
    avatar: str