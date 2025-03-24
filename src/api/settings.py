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
    rq_host: str = "0.0.0.0"
    rq_port: int = 5672
    rq_user:str = "guest"
    rq_password: str = "guest"
    task_queue: str = "task_queue"
    result_queue: str = "result_queue"
    static_folder: str = "static"

    @property
    def rabbitmq_url(self):
        return "amqp://{}:{}@{}/".format(self.rq_user, self.rq_password, self.rq_host)
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
    def static_dir(self) -> Path:
        return self.base_dir / self.static_folder


    class Config:
        env_file = ".env"

settings = Settings()