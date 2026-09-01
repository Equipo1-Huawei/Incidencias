import os
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from src.config import config

_client: Optional[AsyncIOMotorClient] = None

def get_mongo_client() -> AsyncIOMotorClient:
    """Retorna el cliente asíncrono singleton de MongoDB Atlas."""
    global _client
    if _client is None:
        uri = config.MONGODB_ATLAS_URI
        _client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=3000)
    return _client

async def close_mongo_connection():
    """Cierra la conexión al cliente de MongoDB."""
    global _client
    if _client is not None:
        _client.close()
        _client = None

async def init_indexes():
    """Crea los índices necesarios para consultas rápidas de rango."""
    try:
        client = get_mongo_client()
        db = client.get_default_database("triage_db")
        await db.incident_history.create_index([("component", 1), ("timestamp", -1)])
        await db.knowledge_base.create_index([("incident_type", 1)])
    except Exception as e:
        print(f"[WARN] Failed to initialize Mongo indexes: {e}")
