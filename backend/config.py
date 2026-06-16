"""
MarketMind AI Dashboard - Configuration
All API keys and settings loaded from environment variables or .env file.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _env_value(name: str, default: str = "") -> str:
    """Return an env var, treating template placeholders as unset."""
    value = os.getenv(name, default).strip()
    if value.startswith("your_") and value.endswith("_here"):
        return ""
    return value


def _env_bool(name: str, default: bool = False) -> bool:
    """Return a boolean env var using common truthy values."""
    default_text = "true" if default else "false"
    return os.getenv(name, default_text).strip().lower() in {"1", "true", "yes", "on"}


def _flash_model_only(value: str) -> str:
    """Keep the project on the single supported cost-optimized model."""
    return "deepseek-v4-flash" if value != "deepseek-v4-flash" else value


def _thinking_mode(value: str) -> str:
    value = value.strip().lower()
    return value if value in {"enabled", "disabled"} else "disabled"


def _reasoning_effort(value: str) -> str:
    value = value.strip().lower()
    return value if value in {"high", "max"} else "high"


class Settings:
    """Application-wide settings loaded from environment."""

    # ── LLM Configuration ──
    DEEPSEEK_API_KEY: str = _env_value("DEEPSEEK_API_KEY")
    DEEPSEEK_BASE_URL: str = _env_value("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL: str = _flash_model_only(_env_value("DEEPSEEK_MODEL", "deepseek-v4-flash"))
    DEEPSEEK_DEFAULT_THINKING: str = _thinking_mode(
        _env_value("DEEPSEEK_DEFAULT_THINKING", "disabled")
    )
    DEEPSEEK_REASONING_EFFORT: str = _reasoning_effort(
        _env_value("DEEPSEEK_REASONING_EFFORT", "high")
    )
    DEEPSEEK_ENABLE_JSON_MODE: bool = _env_bool("DEEPSEEK_ENABLE_JSON_MODE", True)
    DEEPSEEK_ENABLE_USAGE_TRACE: bool = _env_bool("DEEPSEEK_ENABLE_USAGE_TRACE", True)

    # ── Financial APIs ──
    FINNHUB_API_KEY: str = _env_value("FINNHUB_API_KEY")
    ALPHA_VANTAGE_API_KEY: str = _env_value("ALPHA_VANTAGE_API_KEY")

    # ── API Endpoints ──
    FINNHUB_BASE_URL: str = "https://finnhub.io/api/v1"
    ALPHA_VANTAGE_BASE_URL: str = "https://www.alphavantage.co/query"
    GOOGLE_NEWS_RSS_URL: str = "https://news.google.com/rss/search"
    REDDIT_RSS_TEMPLATE: str = "https://www.reddit.com/r/{subreddit}/search.rss?q={query}&restrict_sr=on&sort=new&t=month"

    # ── Cache Settings ──
    CACHE_TTL_PRICE: int = int(os.getenv("CACHE_TTL_PRICE", "300"))        # 5 minutes
    CACHE_TTL_NEWS: int = int(os.getenv("CACHE_TTL_NEWS", "1800"))         # 30 minutes
    CACHE_TTL_FUNDAMENTALS: int = int(os.getenv("CACHE_TTL_FUNDAMENTALS", "86400"))  # 24 hours
    CACHE_TTL_MACRO: int = int(os.getenv("CACHE_TTL_MACRO", "3600"))       # 1 hour
    CACHE_DIR: Path = Path(__file__).resolve().parent / "cache" / "cache_store"

    # ── Server ──
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8001"))
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]

    # ── Analysis Settings ──
    MAX_NEWS_ARTICLES: int = int(os.getenv("MAX_NEWS_ARTICLES", "15"))
    REDDIT_POST_LIMIT: int = int(os.getenv("REDDIT_POST_LIMIT", "25"))
    AGENT_TIMEOUT: int = int(os.getenv("AGENT_TIMEOUT", "60"))  # seconds per agent
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "2"))

    # ── Logging ──
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    def get_deepseek_chat_url(self) -> str:
        """Return the chat completions URL for official or legacy base URLs."""
        base = self.DEEPSEEK_BASE_URL.rstrip("/")
        if base.endswith("/chat/completions"):
            return base
        return f"{base}/chat/completions"


settings = Settings()


# Validate critical config at startup
def validate_config():
    """Warn about missing API keys but don't crash - graceful degradation."""
    warnings = []
    if not settings.DEEPSEEK_API_KEY:
        warnings.append("[WARN] DEEPSEEK_API_KEY not set - AI agents will not function")
    if not settings.FINNHUB_API_KEY:
        warnings.append("[WARN] FINNHUB_API_KEY not set - stock price/news will use fallback sources")
    if not settings.ALPHA_VANTAGE_API_KEY:
        warnings.append("[WARN] ALPHA_VANTAGE_API_KEY not set - fundamentals will be limited")
    if warnings:
        print("\n".join(warnings))
        print("Set these in a .env file or environment variables.\n")


if __name__ == "__main__":
    validate_config()
    print(f"Cache dir: {settings.CACHE_DIR}")
    print(f"CORS origins: {settings.CORS_ORIGINS}")
