"""Cliente Supabase singleton (PostgreSQL gestionado)."""
from typing import Optional
from supabase import create_client, Client
from src.config import config
from src.logging_config import get_logger

logger = get_logger(__name__)

_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Retorna el cliente singleton de Supabase."""
    global _supabase_client
    if _supabase_client is None:
        if not config.SUPABASE_URL or not config.SUPABASE_KEY:
            logger.warning("supabase.not_configured", hint="SUPABASE_URL and SUPABASE_KEY must be set; falling back to fixtures")
            raise RuntimeError("Supabase not configured")
        _supabase_client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        logger.info("supabase.connected", url=config.SUPABASE_URL)
    return _supabase_client


def is_supabase_available() -> bool:
    """Verifica si Supabase está configurado y accesible."""
    return bool(config.SUPABASE_URL and config.SUPABASE_KEY)
