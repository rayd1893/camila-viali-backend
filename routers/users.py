from fastapi import APIRouter, Depends, HTTPException, Security, UploadFile, File, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from pathlib import Path
from os import getenv
import secrets
import uuid
from models.engine.connection import get_db
from models.user import User
from models.role import Role
from models.password_reset_token import PasswordResetToken
from schemas.user import (
    Users, Login, Token, UserProfileUpdate, UserAdminUpdate,
    ForgotPasswordRequest, ResetPasswordRequest, AvatarOut,
)
from services.email import send_password_reset_email
import bcrypt
import datetime
import jwt
import pytz

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}}
)

PASSWORD_RESET_TOKEN_TTL_MINUTES = 30
FRONTEND_RESET_PASSWORD_URL = getenv("FRONTEND_URL", "http://localhost:4200") + "/reset-password"

AVATAR_DIR = Path("static/avatars")
AVATAR_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
AVATAR_MAX_SIZE_BYTES = 2 * 1024 * 1024  # 2 MB

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


# --- Recuperación de contraseña ---------------------------------------------

@router.post("/password/forgot")
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Genera un token de recuperación y lo envía por correo si el email
    corresponde a un usuario activo. Siempre responde el mismo mensaje
    genérico (exista o no el email) para no revelar qué correos están
    registrados.
    """
    generic_response = {
        'code': 200,
        'message': 'Si el correo está registrado, recibirás un enlace para restablecer tu contraseña.',
    }

    user = db.query(User).where(User.status == True, User.email == request.email).one_or_none()
    if user is None:
        return generic_response

    now = datetime.datetime.utcnow()

    # Invalidar tokens previos no usados de este usuario.
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None),
    ).update({"used_at": now})

    token_value = secrets.token_urlsafe(32)
    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token_value,
        expires_at=now + datetime.timedelta(minutes=PASSWORD_RESET_TOKEN_TTL_MINUTES),
        used_at=None,
        created_at=now,
    )
    db.add(reset_token)
    db.commit()

    reset_url = f"{FRONTEND_RESET_PASSWORD_URL}?token={token_value}"
    try:
        send_password_reset_email(user.email, reset_url)
    except RuntimeError:
        # SMTP no configurado todavia: no bloquear el flujo, pero no fingir
        # que se envio el correo.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='El envío de correos no está configurado en el servidor (faltan variables SMTP_*).',
        )

    return generic_response


@router.post("/password/reset")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Valida el token recibido por correo y actualiza la contraseña."""
    now = datetime.datetime.utcnow()

    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == request.token,
        PasswordResetToken.used_at.is_(None),
        PasswordResetToken.expires_at > now,
    ).one_or_none()

    if reset_token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='El token es inválido o ya venció. Solicita uno nuevo.',
        )

    user = db.query(User).where(User.id == reset_token.user_id).one_or_none()
    if user is None or not user.status:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Usuario no encontrado o inactivo.')

    password_hash = bcrypt.hashpw(request.new_password.encode('utf-8'), bcrypt.gensalt())
    user.password = password_hash.decode('utf-8')
    reset_token.used_at = now
    db.commit()

    return {'code': 200, 'message': 'Contraseña actualizada correctamente.'}


# --- Edición de perfil -------------------------------------------------------

@router.patch("/me")
def update_my_profile(
    request: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    El propio usuario puede editar sus datos (nombre, apellido, username),
    pero NO su email por esta vía. Para cambiar el email de un usuario se
    necesita el permiso 'users:update' (ver PATCH /users/{user_id}).
    """
    updates = request.model_dump(exclude_unset=True)

    if "username" in updates and updates["username"] != current_user.username:
        exists = db.query(User).filter(
            User.username == updates["username"], User.id != current_user.id,
        ).one_or_none()
        if exists is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Ese username ya está en uso.')

    for key, value in updates.items():
        setattr(current_user, key, value)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.patch("/{user_id}")
def update_user_as_admin(
    user_id: int,
    request: UserAdminUpdate,
    db: Session = Depends(get_db),
    authorize: bool = Depends(PermissionChecker('users:update')),
):
    """
    Edición de datos de cualquier usuario por un administrador (requiere el
    permiso 'users:update'). A diferencia de PATCH /users/me, esta sí permite
    cambiar el email, reasignar el rol (role_id) y activar/desactivar la
    cuenta (status).
    """
    user = db.query(User).where(User.id == user_id).one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Usuario no encontrado.')

    updates = request.model_dump(exclude_unset=True)

    if "email" in updates and updates["email"] != user.email:
        exists = db.query(User).filter(User.email == updates["email"], User.id != user.id).one_or_none()
        if exists is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Ese email ya está en uso.')

    if "username" in updates and updates["username"] != user.username:
        exists = db.query(User).filter(User.username == updates["username"], User.id != user.id).one_or_none()
        if exists is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Ese username ya está en uso.')

    if "role_id" in updates and updates["role_id"] != user.role_id:
        role = db.query(Role).where(Role.id == updates["role_id"]).one_or_none()
        if role is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='El role_id indicado no existe.')

    for key, value in updates.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user


# --- Avatar ------------------------------------------------------------------

@router.post("/me/avatar", response_model=AvatarOut)
async def upload_my_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Sube/reemplaza la foto de perfil del usuario autenticado."""
    extension = Path(file.filename or "").suffix.lower()
    if extension not in AVATAR_ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato no permitido. Usa alguno de: {', '.join(sorted(AVATAR_ALLOWED_EXTENSIONS))}",
        )

    content = await file.read()
    if len(content) > AVATAR_MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La imagen supera el tamaño máximo permitido ({AVATAR_MAX_SIZE_BYTES // (1024 * 1024)} MB).",
        )

    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{current_user.id}_{uuid.uuid4().hex}{extension}"
    (AVATAR_DIR / filename).write_bytes(content)

    current_user.avatar = f"/static/avatars/{filename}"
    db.commit()

    return AvatarOut(avatar=current_user.avatar)

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
