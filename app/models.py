from pydantic import BaseModel, EmailStr
from typing import List

# --- MODELOS DE USUARIO ---
class UsuarioCrear(BaseModel):
    username: str
    email: EmailStr
    password: str
    rol: str 

class Token(BaseModel):
    access_token: str
    token_type: str

# --- MODELOS DE CLIENTE ---
class Direccion(BaseModel):
    calle: str
    ciudad: str
    region: str

class ClienteBase(BaseModel):
    nombre: str
    email: EmailStr 
    direccion: Direccion

# --- MODELOS DE PRODUCTO ---
class ProductoCrear(BaseModel):
    nombre: str
    descripcion: str
    precio: float
    stock: int

# --- MODELOS DE PEDIDO ---
class ItemPedido(BaseModel):
    producto_id: str
    cantidad: int
    precio_historico: float 

class PedidoCrear(BaseModel):
    cliente_id: str 
    items: List[ItemPedido]  