from app.config import Settings, settings
from app.modules.ai.base import AIProvider
from app.modules.ai.config_status import ai_is_configured
from app.modules.ai.provider import ChatCompletionsProvider


def build_ai_provider(
    app_settings: Settings | None = None,
    http_client=None,
) -> AIProvider | None:
    cfg = app_settings or settings
    if not ai_is_configured(cfg):
        return None
    return ChatCompletionsProvider(
        base_url=cfg.ai_base_url,
        api_key=cfg.ai_api_key,
        model=cfg.ai_model,
        timeout_seconds=float(cfg.ai_timeout_seconds),
        http_client=http_client,
        max_retries=int(cfg.ai_max_retries),
        retry_backoff_seconds=float(cfg.ai_retry_backoff_ms) / 1000.0,
    )
