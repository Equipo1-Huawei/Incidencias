import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar .env desde la raíz del proyecto o desde el directorio backend
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

class Config:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

    # LLM settings
    PANGU_API_KEY = os.getenv("PANGU_API_KEY", "")
    PANGU_BASE_URL = os.getenv("PANGU_BASE_URL", "https://maas.cn-north-4.myhuaweicloud.com")
    HUAWEI_MODEL = os.getenv("HUAWEI_MODEL", "pangu-40b")

    OPENAI_FALLBACK_KEY = os.getenv("OPENAI_FALLBACK_KEY", "")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

    # DB settings
    MONGODB_ATLAS_URI = os.getenv("MONGODB_ATLAS_URI", "mongodb://localhost:27017")

    # Microservices settings
    NEXTJS_HEALTH_URL = os.getenv("NEXTJS_HEALTH_URL", "http://localhost:3000/api/health")

    # Vector store (Qdrant)
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

    # Agent parameters
    AGENT_TEMPERATURE = 0.2
    AGENT_MAX_TOKENS = 1500
    AGENT_TIMEOUT_SECONDS = 15

    # Guardrails
    MAX_LOOPS = int(os.getenv("MAX_LOOPS", "12"))
    MAX_COST_USD = float(os.getenv("MAX_COST_USD", "1.0"))

    @property
    def has_real_key(self) -> bool:
        return bool(self.PANGU_API_KEY) or bool(self.OPENAI_FALLBACK_KEY)

config = Config()
