from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from app.database import db
from app.models import ClienteBase  
from app.security import obtener_usuario_actual, verificar_permisos

router = APIRouter(prefix="/clientes", tags=["Clientes"])
clientes_collection = db["clientes"]

# 1. CREATE (Crear un cliente nuevo)
@router.post("/", status_code=status.HTTP_201_CREATED)
def crear_cliente(cliente: ClienteBase, usuario=Depends(obtener_usuario_actual)):
    verificar_permisos(usuario, ["Administrador", "Ventas"])
    if clientes_collection.find_one({"email": cliente.email}):
        raise HTTPException(status_code=400, detail="El email ya está registrado")
        
    nuevo_cliente = cliente.model_dump()
    resultado = clientes_collection.insert_one(nuevo_cliente)
    nuevo_cliente["_id"] = str(resultado.inserted_id)
    return nuevo_cliente

# 2. READ ALL (Listar clientes)
@router.get("/")
def listar_clientes(usuario=Depends(obtener_usuario_actual)):
    verificar_permisos(usuario, ["Administrador", "Ventas"])
    clientes = []
    for c in clientes_collection.find():
        c["_id"] = str(c["_id"])
        clientes.append(c)
    return clientes

# 3. READ ONE (Detalle de un cliente específico)
@router.get("/{cliente_id}")
def obtener_cliente(cliente_id: str, usuario=Depends(obtener_usuario_actual)):
    verificar_permisos(usuario, ["Administrador", "Ventas"])
    if not ObjectId.is_valid(cliente_id):
        raise HTTPException(status_code=400, detail="ID inválido")
    cliente = clientes_collection.find_one({"_id": ObjectId(cliente_id)})
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    cliente["_id"] = str(cliente["_id"])
    return cliente

# 4. UPDATE (Actualizar cliente)
@router.put("/{cliente_id}")
def actualizar_cliente(cliente_id: str, cliente: ClienteBase, usuario=Depends(obtener_usuario_actual)):
    verificar_permisos(usuario, ["Administrador", "Ventas"])
    if not ObjectId.is_valid(cliente_id):
        raise HTTPException(status_code=400, detail="ID inválido")
    datos_actualizar = cliente.model_dump()
    resultado = clientes_collection.update_one({"_id": ObjectId(cliente_id)}, {"$set": datos_actualizar})
    if resultado.matched_count == 0:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    datos_actualizar["_id"] = cliente_id
    return {"mensaje": "Cliente actualizado", "cliente": datos_actualizar}

# 5. DELETE (Eliminar cliente)
@router.delete("/{cliente_id}")
def eliminar_cliente(cliente_id: str, usuario=Depends(obtener_usuario_actual)):
    verificar_permisos(usuario, ["Administrador"])
    if not ObjectId.is_valid(cliente_id):
        raise HTTPException(status_code=400, detail="ID inválido")
    resultado = clientes_collection.delete_one({"_id": ObjectId(cliente_id)})
    if resultado.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return {"mensaje": "Cliente eliminado"}