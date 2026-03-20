from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str = "sqlite:///./gxp_platform.db"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    default_rate_limit_per_minute: int = 10
    free_plan_daily_limit: int = 5
    pro_plan_daily_limit: int = 300
    team_plan_daily_limit: int = 3000
    admin_user_ids: str = ""

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "gxp_docs"
    redis_url: str = "redis://localhost:6379/0"
    s3_bucket: str = "gxp-docs"

    embedding_model: str = "BAAI/bge-m3"
    embedding_local_files_only: bool = True
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    openai_timeout_seconds: int = 20
    ollama_enabled: bool = False
    ollama_model: str = "qwen2.5:7b-instruct"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_num_predict: int = 160
    ollama_num_ctx: int = 2048
    ollama_temperature: float = 0.1
    answer_cache_ttl_seconds: int = 3600
    internet_fallback_enabled: bool = False
    internet_fallback_timeout_seconds: int = 8
    internet_fallback_max_results: int = 3
    internet_fallback_min_confidence: float = 0.45
    internet_fallback_domains: str = (
        "who.int,ema.europa.eu,edqm.eu,gov.uk,fda.gov,ich.org,picscheme.org,ec.europa.eu,codexalimentarius.fao.org"
    )
    answer_review_log_path: str = "logs/answer_review.jsonl"
    answer_review_slow_seconds: float = 12.0
    answer_review_low_confidence: float = 0.55

    admin_emails: str = "admin@example.com"
    telegram_admin_user_ids: str = ""
    legal_disclaimer_enabled: bool = True
    legal_disclaimer_vi: str = (
        "Tuyen ngon: Noi dung chi mang tinh tham khao thong tin, khong thay the tu van phap ly/QA chinh thuc. "
        "Quyet dinh van hanh va tuan thu thuoc ve don vi phu trach."
    )
    legal_disclaimer_en: str = (
        "Disclaimer: This content is for informational purposes only and does not replace formal legal/QA advice. "
        "Final compliance decisions remain with your responsible organization."
    )

    telegram_bot_token: str = ""
    telegram_webhook_secret: str = ""
    telegram_webhook_url: str = ""
    telegram_bot_mode: str = "webhook"  # webhook | polling
    telegram_stars_enabled: bool = True
    telegram_pro_price_stars: int = 199
    telegram_pro_title: str = "GxP Bot Pro (30 days)"
    telegram_pro_description: str = "Upgrade to Pro plan for 30 days."

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
