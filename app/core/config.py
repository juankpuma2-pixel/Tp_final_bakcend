from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Configuración de Proyecto y Base de Datos (SQLite local por defecto)
    PROJECT_NAME: str = "API E-Commerce IRESM"
    DATABASE_URL: str = "sqlite:///./tienda.db"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Configuración de Seguridad y JWT
    SECRET_KEY: str = "clave_secreta_super_segura_para_desarrollo_iresm_2026"
    ALGORITHM: str = "HS256"
    ACCESS_MIN: int = 30
    REFRESH_MIN: int = 10080

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    class Config:
        env_file = ".env"

settings = Settings()
