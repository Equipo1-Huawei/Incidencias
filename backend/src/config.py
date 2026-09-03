import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

class Config:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

    # LLM settings (Kostra/Huawei MaaS — OpenAI compatible)
    PANGU_API_KEY = os.getenv("PANGU_API_KEY", "")
    PANGU_BASE_URL = os.getenv("PANGU_BASE_URL", "https://ai.kostra.cloud/v1")
    HUAWEI_MODEL = os.getenv("HUAWEI_MODEL", "glm-5.2")

    OPENAI_FALLBACK_KEY = os.getenv("OPENAI_FALLBACK_KEY", "")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

    # Supabase settings
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")

    # Threat Intel
    VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY", "")
    ABUSEIPDB_API_KEY = os.getenv("ABUSEIPDB_API_KEY", "")

    # Vector store
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

    # Microservices settings
    NEXTJS_HEALTH_URL = os.getenv("NEXTJS_HEALTH_URL", "http://localhost:3000/api/health")

    # Agent parameters
    AGENT_TEMPERATURE = float(os.getenv("AGENT_TEMPERATURE", "0.2"))
    AGENT_MAX_TOKENS = int(os.getenv("AGENT_MAX_TOKENS", "1500"))
    AGENT_TIMEOUT_SECONDS = float(os.getenv("AGENT_TIMEOUT_SECONDS", "60"))

    # Guardrails
    MAX_LOOPS = int(os.getenv("MAX_LOOPS", "12"))
    MAX_COST_USD = float(os.getenv("MAX_COST_USD", "1.0"))

    # Webhook security
    WEBHOOK_API_KEY = os.getenv("WEBHOOK_API_KEY", "")
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8501,http://localhost:3000").split(",")

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @property
    def has_real_key(self) -> bool:
        return bool(self.PANGU_API_KEY and self.PANGU_API_KEY.startswith("sk-"))

config = Config()
