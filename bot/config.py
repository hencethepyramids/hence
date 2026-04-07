from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    discord_token: str
    discord_guild_id: int
    api_base_url: str = "http://localhost:8000"
    alerts_channel_name: str = "ark-alerts"


settings = Settings()
