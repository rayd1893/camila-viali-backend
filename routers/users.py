from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from models.engine.connection import get_db
from models.user import User
from schemas.user import Users, Login, Token
import bcrypt
import datetime
import jwt
import pytz

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}}
)

oauth_scheme = OAuth2PasswordBearer(
    tokenUrl="token"
)

def authenticate_user(username: str, password: str, db: Session):
    exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Credenciales incorrectas'
    )

    user = db.query(User).where(User.status == True, 
                                or_(User.email == username, User.username == username)
                                ).one_or_none()
    if user is None:
        raise exception

    if not bcrypt.checkpw(password.encode(), user.password.encode()):
        raise exception
    
    user.role.permissions
    delattr(user, 'password')
    
    return user

def create_token(user):
    payload = {'sub': user.username, 'iat': datetime.datetime.now(pytz.timezone('UTC')),
               'exp': datetime.datetime.now(pytz.timezone('UTC')) + datetime.timedelta(minutes=90)}
    token = jwt.encode(payload, key='secret')
    print(payload)
    return token 



def get_current_user(token: str = Depends(oauth_scheme), db: Session = Depends(get_db)):
    decoded = jwt.decode(token, 'secret', algorithms=['HS256'])
    username = (decoded['sub'])
    user = db.query(User).where(User.status == True, 
                                User.username == username
                                ).one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid credentials'
        )
    
    user.role.permissions
    return user

class PermissionChecker:

    def __init__(self, required_permissions: str) -> None:
        self.required_permissions = required_permissions

    def __call__(self, user = Depends(get_current_user)) -> bool:

        for p in user.role.permissions:
            if self.required_permissions == p.permission:
                return True

        raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='Permissions'
                )

@router.get("/me")
def get_user(current_user = Depends(get_current_user)):
    return current_user

@router.post("/login")
def login(login: Login, db: Session= Depends(get_db)):
    user = authenticate_user(login.username, login.password, db)
    token_str = create_token(user)
    token = Token(access_token=token_str, token_type='bearer')
    return token


@router.get("/")
async def read_users(db: Session= Depends(get_db)):
    users = db.query(User).where(User.status == True).all()
    for user in users:
        user.role.permissions
    return users

@router.post("/")
def create_user(user: Users, db: Session = Depends(get_db)):
    new_user = User(**user.model_dump())
    password = new_user.password
    bytes = password.encode('utf-8')
    salt = bcrypt.gensalt() 
    password_hash = bcrypt.hashpw(bytes, salt)
    new_user.password = password_hash
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/{username}")
async def read_user(username: str):
    return {"username": username}
