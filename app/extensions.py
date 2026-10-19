from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from authlib.integrations.flask_client import OAuth

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
oauth = OAuth()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["600 per hour"],
    storage_uri="memory://",
)

login_manager.login_view = "auth.login"
login_manager.login_message = "Faça login para acessar esta área."
login_manager.login_message_category = "info"
