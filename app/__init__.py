import os
from datetime import datetime, timezone
from flask import Flask, render_template, request, make_response
from flask_login import current_user
from werkzeug.middleware.proxy_fix import ProxyFix
from app.config import Config
from app.extensions import db, login_manager, csrf, oauth, limiter
from app.models import User, Category, Post, Service, Setting
from app.seed import run_seed


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Suporte a cabeçalhos X-Forwarded-* do Nginx Proxy Manager
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Inicialização das extensões
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    oauth.init_app(app)
    limiter.init_app(app)

    # Registro do provedor Google OAuth 2.0
    oauth.register(
        name="google",
        client_id=app.config.get("GOOGLE_CLIENT_ID"),
        client_secret=app.config.get("GOOGLE_CLIENT_SECRET"),
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Registro dos Blueprints
    from app.routes.public import public_bp
    from app.routes.blog import blog_bp
    from app.routes.auth import auth_bp
    from app.routes.client import client_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(blog_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(client_bp)
    app.register_blueprint(admin_bp)

    # Criação automática de tabelas e Seed inicial
    with app.app_context():
        try:
            db.create_all()
            run_seed()
        except Exception as exc:
            app.logger.warning(f"Aviso ao inicializar banco/seed: {exc}")

    # Context Processor global (Rodapé, Topbar, Categorias, Arquivos do Blog)
    @app.context_processor
    def inject_globals():
        setting = Setting.query.first()
        footer_categories = Category.query.order_by(Category.name.asc()).all()
        footer_services = (
            Service.query.filter_by(is_active=True)
            .order_by(Service.display_order.asc())
            .limit(6)
            .all()
        )
        is_maintenance = bool(
            (setting and setting.maintenance_mode)
            or app.config.get("MAINTENANCE_MODE", False)
        )
        return {
            "site_setting": setting,
            "footer_categories": footer_categories,
            "footer_services": footer_services,
            "is_maintenance_active": is_maintenance,
            "current_year": datetime.now(timezone.utc).year,
        }

    # Middleware de Modo de Manutenção Programada (HTTP 503 SEO Friendly)
    @app.before_request
    def check_maintenance_mode():
        path = request.path or "/"
        allowed_prefixes = (
            "/static/",
            "/auth/",
            "/admin",
            "/health",
            "/manifest.json",
            "/robots.txt",
        )
        if any(path.startswith(prefix) for prefix in allowed_prefixes):
            return None

        setting = Setting.query.first()
        is_maintenance = bool(
            (setting and setting.maintenance_mode)
            or app.config.get("MAINTENANCE_MODE", False)
        )
        if not is_maintenance:
            return None

        # Bypass para administradores logados
        if current_user.is_authenticated and current_user.is_admin:
            return None

        resp = make_response(
            render_template("public/maintenance.html", site_setting=setting), 503
        )
        resp.headers["Retry-After"] = "3600"
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        return resp

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("public/404.html"), 404

    @app.errorhandler(429)
    def ratelimit_handler(error):
        return (
            render_template(
                "public/404.html",
                error_title="Muitas tentativas em sequência",
                error_message="Por segurança, aguarde um minuto antes de tentar novamente.",
            ),
            429,
        )

    return app
