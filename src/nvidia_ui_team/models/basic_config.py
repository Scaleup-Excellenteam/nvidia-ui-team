from pydantic import BaseSettings

class BasicAPIConfig(BaseSettings):
    _env_prefix = "API_"
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
