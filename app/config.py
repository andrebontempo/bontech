import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuração centralizada da aplicação Bontech (Flask)."""

    SECRET_KEY = os.getenv("SECRET_KEY", "bontech_chave_super_secreta_corporativa_2026")
    _raw_db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://bontech:bontech_secret_2026@db:5432/bontech",
    )
    if _raw_db_url.startswith("postgres://"):
        _raw_db_url = _raw_db_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif _raw_db_url.startswith("postgresql://"):
        _raw_db_url = _raw_db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    SQLALCHEMY_DATABASE_URI = _raw_db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # Sessão & Cookies
    PERMANENT_SESSION_LIFETIME = timedelta(days=14)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # URLs e Upload
    BASE_URL = os.getenv("BASE_URL", "https://bontech.com.br").rstrip("/")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB
    UPLOAD_FOLDER = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "static", "uploads"
    )

    # Google OAuth 2.0
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_CALLBACK_URL = os.getenv(
        "GOOGLE_CALLBACK_URL", f"{BASE_URL}/auth/google/callback"
    )

    # E-mail SMTP
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.hostinger.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
    SMTP_USER = os.getenv("SMTP_USER", "suporte@bontech.com.br")
    SMTP_PASS = os.getenv("SMTP_PASS", "")
    SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Bontech TI & Governança")
    ADMIN_ALERT_EMAIL = os.getenv("ADMIN_ALERT_EMAIL", "suporte@bontech.com.br")

    # Webhook n8n opcional
    N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")

    # Administrador Inicial (Seed)
    ADMIN_NAME = os.getenv("ADMIN_NAME", "André Bontempo")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "suporte@bontech.com.br")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Bontech@2026")

    # Modo de Manutenção via ENV
    MAINTENANCE_MODE = os.getenv("MAINTENANCE_MODE", "false").lower() in (
        "true",
        "1",
        "yes",
    )
