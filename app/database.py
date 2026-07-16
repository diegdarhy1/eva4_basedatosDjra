import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Cargar las variables de entorno de forma correcta
load_dotenv() 


MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:password@127.0.0.1:27017/?authSource=admin")


client = MongoClient(MONGO_URI)
db = client["comerciotech_db"]

usuarios_collection = db["usuarios"]
productos_collection = db["productos"]
pedidos_collection = db["pedidos"]
clientes_collection = db["clientes"]