from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./daybook.db"
    secret_key: str = "dev-only-change-me"
    internal_api_url: str = "http://api:8000"      # where the bot process reaches the API inside the compose network
    access_token_minutes: int = 60 * 12
    require_2fa_roles: str = ""           # e.g. "admin,acc": these roles must set up two-factor sign-in before they can use the system
    cors_origins: str = "*"
    seed_demo_users: bool = False
    admin_username: str = "admin"
    admin_password: str = ""      # if set and there are no users yet, the seed creates this administrator
    frontend_dir: str = "../frontend"
    # AI (Claude). Without a key the AI screens still work from the database, only the written answers are simpler.
    ai_provider: str = "auto"             # auto | anthropic | gemini  (auto: whichever key is set, Anthropic first)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    gemini_base_url: str = "https://generativelanguage.googleapis.com"
    anthropic_api_key: str = ""
    ai_model: str = "claude-sonnet-5-5"
    ai_base_url: str = "https://api.anthropic.com"
    ai_timeout: int = 90
    ai_rate_per_10min: int = 40           # requests per user to the model
    # Telegram bot (optional). The token comes from @BotFather and lives only here, on the server.
    telegram_bot_token: str = ""
    telegram_bot_username: str = ""       # without @, only used to show the link in the web app
    telegram_api_base: str = "https://api.telegram.org"
    telegram_alert_minutes: int = 30
    telegram_digest_hour: int = 18        # the daily summary goes out at this hour, local time
    backup_dir: str = "/backups"          # where the backup container writes (mounted read-only into the bot)
    telegram_send_backups: bool = True    # send every verified, encrypted backup to the admins' Telegram chats
    telegram_utc_offset: int = 5          # local time = UTC + this many hours (Uzbekistan: 5)
    bank_allow_negative: bool = False     # true: a payment may take a bank account below zero (overdraft). Cash desks never may.
    ai_company: str = ""                  # optional one-liner about the business, added to the prompts


settings = Settings()
