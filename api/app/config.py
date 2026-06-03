from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://ontologyready:ontologyready@localhost:5432/ontologyready"
    db_pool_min: int = 5
    db_pool_max: int = 20
    host: str = "0.0.0.0"
    port: int = 8000
    api_key: str = ""
    jwt_secret: str = ""
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    model_config = {"env_file": "../.env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
