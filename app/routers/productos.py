from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId 
from app.database import productos_collection
from app.models import ProductoCrear
from app.security import obtener_usuario_actual, verificar_permisos

router = APIRouter(prefix="/productos", tags=["Catálogo"])

# 1. CREATE (Crear un producto)
@router.post("/", status_code=status.HTTP_201_CREATED)
def crear_producto(producto: ProductoCrear, usuario=Depends(obtener_usuario_actual)):
    verificar_permisos(usuario, ["Administrador", "Ventas"])
    
    nuevo_producto = producto.model_dump()
    resultado = productos_collection.insert_one(nuevo_producto)
    nuevo_producto["_id"] = str(resultado.inserted_id)
    return nuevo_producto

# 2. READ ALL (Listar todos los productos)
@router.get("/")
def listar_productos():
    productos = []
    for p in productos_collection.find():
        p["_id"] = str(p["_id"])
        productos.append(p)
    return productos

# 3. READ ONE (Buscar un producto por su ID)
@router.get("/{producto_id}")
def obtener_producto(producto_id: str):
    # Validar que la ID tenga el formato correcto de Mongo
    if not ObjectId.is_valid(producto_id):
        raise HTTPException(status_code=400, detail="ID de producto inválido")
        
    producto = productos_collection.find_one({"_id": ObjectId(producto_id)})
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
        
    producto["_id"] = str(producto["_id"])
    return producto

# 4. UPDATE (Actualizar un producto existente)
@router.put("/{producto_id}")
def actualizar_producto(producto_id: str, producto: ProductoCrear, usuario=Depends(obtener_usuario_actual)):
    verificar_permisos(usuario, ["Administrador", "Ventas"])
    
    if not ObjectId.is_valid(producto_id):
        raise HTTPException(status_code=400, detail="ID inválido")
    
    datos_actualizar = producto.model_dump()
    resultado = productos_collection.update_one(
        {"_id": ObjectId(producto_id)}, 
        {"$set": datos_actualizar}
    )
    
    if resultado.matched_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    datos_actualizar["_id"] = producto_id
    return {"mensaje": "Producto actualizado", "producto": datos_actualizar}

# 5. DELETE (Eliminar un producto)
@router.delete("/{producto_id}")
def eliminar_producto(producto_id: str, usuario=Depends(obtener_usuario_actual)):
    verificar_permisos(usuario, ["Administrador"]) 
    
    if not ObjectId.is_valid(producto_id):
        raise HTTPException(status_code=400, detail="ID inválido")
        
    resultado = productos_collection.delete_one({"_id": ObjectId(producto_id)})
    
    if resultado.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
        
    return {"mensaje": "Producto eliminado exitosamente"}