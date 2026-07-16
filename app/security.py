import os
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "clave_por_defecto_segura")
ALGORITHM = "HS256"

# Configuración de hashing y esquema de autenticación para Swagger UI
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# --- FUNCIONES DE CONTRASEÑAS ---
def hashear_password(password: str):
    return pwd_context.hash(password)

def verificar_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

# --- FUNCIONES DE TOKEN (JWT) ---
def crear_token_acceso(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- FUNCIONES DE VALIDACIÓN DE RUTAS ---
def obtener_usuario_actual(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        rol: str = payload.get("rol")
        if username is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return {"username": username, "rol": rol}
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expirado o inválido")

def verificar_permisos(usuario: dict = Depends(obtener_usuario_actual), roles_permitidos: list = []):
    """
    Se usa en los endpoints para bloquear el acceso si el rol no coincide.
    """
    if usuario["rol"] not in roles_permitidos:
        raise HTTPException(status_code=403, detail="No tienes permisos para esta acción")
    return usuario