from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "DEBUG"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    app_name: str = "MetaSimulator API"
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False
    db_name: str = "metasimulator"
    db_username: str = "metasimulator"
    db_password: str = "metasimulator"
    db_host: str = "localhost"
    db_port: int = 5432
    rabbitmq_url: str = "amqp://guest:guest@localhost/"
    task_queue: str = "task_queue"
    result_queue: str = "result_queue"
    @property
    def db_url(self) -> str:
        return "postgresql+asyncpg://{}:{}@{}:{}/{}".format(self.db_username,
                                                            self.db_password,
                                                            self.db_host,
                                                            self.db_port,
                                                            self.db_name)

    class Config:
        env_file = ".env"

settings = Settings()