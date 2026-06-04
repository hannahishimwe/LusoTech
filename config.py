import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class NoxusConfig:
    api_key: str
    base_url: str = "https://backend.noxus.ai"
    timeout: int = 30
    retries: int = 3

@dataclass
class SupabaseConfig:
    url: str
    key: str

def get_noxus_config() -> NoxusConfig:
    return NoxusConfig(
        api_key=os.getenv("NOXUS_API_KEY", ""),
        base_url=os.getenv("NOXUS_BACKEND_URL", "https://backend.noxus.ai"),
        timeout=int(os.getenv("NOXUS_TIMEOUT", "30")),
        retries=int(os.getenv("NOXUS_RETRIES", "3"))
    )

def get_supabase_config() -> SupabaseConfig:
    return SupabaseConfig(
        url=os.getenv("SUPABASE_URL", ""),
        key=os.getenv("SUPABASE_KEY", "")
    )