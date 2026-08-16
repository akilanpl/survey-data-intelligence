from app.config import Settings, settings


def ai_is_configured(app_settings: Settings | None = None) -> bool:
    cfg = app_settings or settings
    return bool(cfg.ai_base_url and cfg.ai_api_key and cfg.ai_model)


def ai_model_configured(app_settings: Settings | None = None) -> bool:
    cfg = app_settings or settings
    return bool(cfg.ai_model)
