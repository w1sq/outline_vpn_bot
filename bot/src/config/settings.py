from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongo_uri: SecretStr
    db_name: SecretStr
    tg_token: SecretStr
    admin_users: SecretStr

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


config = Settings()
