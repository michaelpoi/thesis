from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    SECRET_KEY: str = "DEBUG"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    app_name: str = "MetaSimulator API"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    db_name: str = "metasimulator"
    db_username: str = "metasimulator"
    db_password: str = "metasimulator"
    db_host: str = "0.0.0.0"
    db_port: int = 5432
    blobs_folder: str = "blobs"
    maps_folder: str = "maps"
    logs_folder: str = "logs"


    @property
    def db_url(self) -> str:
        return "postgresql+asyncpg://{}:{}@{}:{}/{}".format(self.db_username,
                                                            self.db_password,
                                                            self.db_host,
                                                            self.db_port,
                                                            self.db_name)

    @property
    def base_dir(self) -> Path:
        return Path(__file__).resolve().parent

    @property
    def blobs_dir(self) -> Path:
        return self.base_dir / self.blobs_folder
    
    @property
    def maps_dir(self) -> Path:
        return self.base_dir / self.maps_folder
    
    @property
    def logs_dir(self) -> Path:
        return self.base_dir / self.logs_folder


    class Config:
        env_file = ".env"

settings = Settings()