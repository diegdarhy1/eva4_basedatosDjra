from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

from app.database import usuarios_collection
from app.models import UsuarioCrear, Token
from app.security import hashear_password, verificar_password, crear_token_acceso

router = APIRouter(tags=["Autenticación"])

@router.post("/usuarios/", status_code=status.HTTP_201_CREATED)
def crear_usuario(usuario: UsuarioCrear):
    if usuarios_collection.find_one({"username": usuario.username}):
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    
    usuario_dict = usuario.model_dump()
    
    usuario_dict["rol"] = "Usuario Registrado"
    
    usuario_dict["password"] = hashear_password(usuario_dict["password"])
    
    usuarios_collection.insert_one(usuario_dict)
    return {"mensaje": f"Usuario {usuario.username} creado exitosamente con el rol 'Usuario Registrado'"}

@router.post("/login", response_model=Token)
def iniciar_sesion(form_data: OAuth2PasswordRequestForm = Depends()):
    usuario_db = usuarios_collection.find_one({"username": form_data.username})
    
    if not usuario_db or not verificar_password(form_data.password, usuario_db["password"]):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    token_data = {"sub": usuario_db["username"], "rol": usuario_db["rol"]}
    token = crear_token_acceso(data=token_data, expires_delta=timedelta(minutes=60))
    
    return {"access_token": token, "token_type": "bearer"}