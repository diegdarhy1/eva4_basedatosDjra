import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Búsqueda automática y segura del archivo .env
load_dotenv()
uri = os.getenv("MONGO_URI")

print(f"DEBUG: Intentando conectar con URI: {uri}")

try:
    client = MongoClient(uri)
    # Ping al servidor para verificar autenticación y estado
    client.admin.command('ping')
    print("\n¡ÉXITO! Conexión a MongoDB establecida correctamente.")
except Exception as e:
    print(f"\nERROR: Fallo de autenticación o conexión. Detalle: {e}")