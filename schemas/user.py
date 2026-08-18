from pydantic import BaseModel, EmailStr

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