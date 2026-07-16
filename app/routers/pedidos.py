from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List
from datetime import datetime, timezone  
from bson import ObjectId
from app.database import db
from app.security import obtener_usuario_actual, verificar_permisos

router = APIRouter(prefix="/pedidos", tags=["Ventas"])
pedidos_collection = db["pedidos"]
productos_collection = db["productos"]

# --- MODELOS DE PEDIDO ---
class ItemPedido(BaseModel):
    producto_id: str
    cantidad: int
    precio_historico: float

class PedidoBase(BaseModel):
    cliente_id: str  
    items: List[ItemPedido] 

# 1. CREATE (Generar un nuevo pedido con validación de stock)
@router.post("/", status_code=status.HTTP_201_CREATED)
def crear_pedido(pedido: PedidoBase, usuario=Depends(obtener_usuario_actual)):
    verificar_permisos(usuario, ["Administrador", "Ventas", "Usuario Registrado"])
    
    
    for item in pedido.items:
        if not ObjectId.is_valid(item.producto_id):
            raise HTTPException(status_code=400, detail=f"El ID del producto {item.producto_id} no tiene un formato válido.")
            
        producto_db = productos_collection.find_one({"_id": ObjectId(item.producto_id)})
        
        if not producto_db:
            raise HTTPException(status_code=404, detail=f"El producto con ID {item.producto_id} no existe.")

        stock_actual = producto_db.get("stock", 0)
        if item.cantidad > stock_actual:
            raise HTTPException(
                status_code=400, 
                detail=f"Stock insuficiente para '{producto_db.get('nombre')}'. Solicitado: {item.cantidad}, Disponible: {stock_actual}."
            )

    # --- FASE 2: CÁLCULO Y CREACIÓN DEL PEDIDO ---
    total_pedido = sum(item.precio_historico * item.cantidad for item in pedido.items)
        
    nuevo_pedido = {
        "cliente_id": pedido.cliente_id,
        "items": [item.model_dump() for item in pedido.items],
        "total": total_pedido,
        "fecha": datetime.now(timezone.utc)  # <-- Corregido: Uso de timezone.utc compatible con Python 3.12
    }
    
    resultado = pedidos_collection.insert_one(nuevo_pedido)

    # --- FASE 3: ACTUALIZACIÓN AUTOMÁTICA DE INVENTARIO ---
    for item in pedido.items:
        productos_collection.update_one(
            {"_id": ObjectId(item.producto_id)}, 
            {"$inc": {"stock": -item.cantidad}}
        )

    return {
        "mensaje": "Pedido generado exitosamente y stock actualizado", 
        "id_pedido": str(resultado.inserted_id), 
        "total_pagado": total_pedido
    }

# 2. READ ALL (Listar el historial de ventas)
@router.get("/")
def listar_pedidos(usuario=Depends(obtener_usuario_actual)):
    verificar_permisos(usuario, ["Administrador", "Ventas"])
    
    pedidos = []
    for p in pedidos_collection.find():
        p["_id"] = str(p["_id"])
        if "fecha" in p:
            p["fecha"] = p["fecha"].isoformat()
        pedidos.append(p)
    return pedidos

# 3. READ ONE (Ver el detalle de un pedido específico)
@router.get("/{pedido_id}")
def obtener_pedido(pedido_id: str, usuario=Depends(obtener_usuario_actual)):
    verificar_permisos(usuario, ["Administrador", "Ventas", "Usuario Registrado"])
    
    if not ObjectId.is_valid(pedido_id):
        raise HTTPException(status_code=400, detail="Formato de ID de pedido inválido")
        
    pedido = pedidos_collection.find_one({"_id": ObjectId(pedido_id)})
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
        
    pedido["_id"] = str(pedido["_id"])
    if "fecha" in pedido:
        pedido["fecha"] = pedido["fecha"].isoformat()
    return pedido

# 4. UPDATE (Modificar un pedido con recalibración de Stock y Rollback)
@router.put("/{pedido_id}")
def actualizar_pedido(pedido_id: str, pedido: PedidoBase, usuario=Depends(obtener_usuario_actual)):
    verificar_permisos(usuario, ["Administrador", "Ventas"])
    
    if not ObjectId.is_valid(pedido_id):
        raise HTTPException(status_code=400, detail="Formato de ID inválido")
        
    
    pedido_viejo = pedidos_collection.find_one({"_id": ObjectId(pedido_id)})
    if not pedido_viejo:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
        
    # --- PASO 1: DEVOLVER TEMPORALMENTE EL STOCK DEL PEDIDO ANTERIOR ---
    for item in pedido_viejo.get("items", []):
        productos_collection.update_one(
            {"_id": ObjectId(item["producto_id"])},
            {"$inc": {"stock": item["cantidad"]}}
        )
        
    # --- PASO 2: VALIDAR EL STOCK DE LOS NUEVOS ITEMS ---
    errores = []
    for item in pedido.items:
        if not ObjectId.is_valid(item.producto_id):
            errores.append(f"El ID del producto {item.producto_id} no es válido.")
            continue
            
        producto_db = productos_collection.find_one({"_id": ObjectId(item.producto_id)})
        if not producto_db:
            errores.append(f"El producto {item.producto_id} no existe.")
            continue
            
        stock_disponible = producto_db.get("stock", 0)
        if item.cantidad > stock_disponible:
            errores.append(
                f"Stock insuficiente para '{producto_db.get('nombre')}'. Requerido: {item.cantidad}, Disponible con retorno: {stock_disponible}"
            )
            
    # --- PASO 3: SI FALLA LA VALIDACIÓN, HACEMOS ROLLBACK ---
    if errores:
        for item in pedido_viejo.get("items", []):
            productos_collection.update_one(
                {"_id": ObjectId(item["producto_id"])},
                {"$inc": {"stock": -item["cantidad"]}}  # Devolvemos la DB a su estado original
            )
        raise HTTPException(status_code=400, detail={"mensaje": "Error de stock al actualizar", "errores": errores})
        
    # --- PASO 4: SI LA VALIDACIÓN PASÓ, DESCONTAMOS EL NUEVO STOCK ---
    for item in pedido.items:
        productos_collection.update_one(
            {"_id": ObjectId(item.producto_id)},
            {"$inc": {"stock": -item.cantidad}}
        )
        
    # --- PASO 5: GUARDAR LOS NUEVOS DATOS DEL PEDIDO ---
    nuevo_total = sum(item.precio_historico * item.cantidad for item in pedido.items)
    
    datos_actualizar = {
        "cliente_id": pedido.cliente_id,
        "items": [item.model_dump() for item in pedido.items],
        "total": nuevo_total,
    }
    
    pedidos_collection.update_one(
        {"_id": ObjectId(pedido_id)}, 
        {"$set": datos_actualizar}
    )
    
    return {"mensaje": "Pedido actualizado y stock reajustado exitosamente", "nuevo_total": nuevo_total}

# 5. DELETE (Anular un pedido y regresar el stock al inventario)
@router.delete("/{pedido_id}")
def eliminar_pedido(pedido_id: str, usuario=Depends(obtener_usuario_actual)):
    verificar_permisos(usuario, ["Administrador"])
    
    if not ObjectId.is_valid(pedido_id):
        raise HTTPException(status_code=400, detail="Formato de ID inválido")
        
    # Buscar el pedido para saber qué productos devolver al catálogo
    pedido = pedidos_collection.find_one({"_id": ObjectId(pedido_id)})
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
        
    
    for item in pedido.get("items", []):
        productos_collection.update_one(
            {"_id": ObjectId(item["producto_id"])},
            {"$inc": {"stock": item["cantidad"]}}
        )
        
    
    pedidos_collection.delete_one({"_id": ObjectId(pedido_id)})
    
    return {"mensaje": "Pedido anulado correctamente, stock devuelto al inventario"}