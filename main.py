from fastapi import FastAPI
from app.routers import productos, clientes, pedidos, usuarios

app = FastAPI(title="API REST ComercioTech - Modular", version="2.0")

# Conectamos todos los archivos de rutas al núcleo de la API
app.include_router(usuarios.router)
app.include_router(productos.router)
app.include_router(clientes.router)
app.include_router(pedidos.router)

@app.get("/", tags=["Inicio"])
def raiz():
    return {"mensaje": "API ComercioTech Operativa. Visita /docs para la documentación."}