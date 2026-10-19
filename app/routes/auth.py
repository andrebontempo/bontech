import secrets
from datetime import datetime, timedelta, timezone
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db, oauth, limiter
from app.models import User, ConsultationRequest, Setting
from app.utils.mail import send_email, trigger_n8n_webhook

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _link_orphan_consultations(user: User):
    """Vincula solicitações anteriores abertas com o mesmo e-mail ao usuário autenticado."""
    orphans = ConsultationRequest.query.filter_by(
        email=user.email.lower(), user_id=None
    ).all()
    for item in orphans:
        item.user_id = user.id


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("15 per minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("client.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("E-mail ou senha inválidos. Verifique suas credenciais.", "danger")
            return render_template("auth/login.html", email=email)

        if not user.is_active_account:
            flash("Sua conta está temporariamente desativada. Entre em contato com o suporte.", "warning")
            return render_template("auth/login.html", email=email)

        user.last_login = datetime.now(timezone.utc)
        _link_orphan_consultations(user)
        db.session.commit()

        login_user(user, remember=remember)
        flash(f"Bem-vindo(a) de volta, {user.name}!", "success")

        next_page = request.args.get("next")
        if next_page and next_page.startswith("/"):
            return redirect(next_page)
        if user.is_admin:
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("client.dashboard"))

    return render_template("auth/login.html")


@auth_bp.route("/cadastro", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("client.dashboard"))

    if request.method == "POST":
        # Honeypot anti-bot
        if request.form.get("website_url"):
            return redirect(url_for("auth.login"))

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        company = request.form.get("company", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("Preencha todos os campos obrigatórios.", "danger")
            return render_template(
                "auth/register.html",
                name=name,
                email=email,
                phone=phone,
                company=company,
            )

        if len(password) < 6:
            flash("A senha deve ter pelo menos 6 caracteres.", "danger")
            return render_template(
                "auth/register.html",
                name=name,
                email=email,
                phone=phone,
                company=company,
            )

        if password != confirm_password:
            flash("As senhas informadas não coincidem.", "danger")
            return render_template(
                "auth/register.html",
                name=name,
                email=email,
                phone=phone,
                company=company,
            )

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash("Já existe uma conta cadastrada com este e-mail. Faça login.", "warning")
            return redirect(url_for("auth.login"))

        user = User(
            name=name,
            email=email,
            phone=phone,
            company=company,
            role="client",
            is_active_account=True,
            last_login=datetime.now(timezone.utc),
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        _link_orphan_consultations(user)
        db.session.commit()

        login_user(user, remember=True)

        # E-mail de boas-vindas
        send_email(
            to_email=user.email,
            subject="Bem-vindo(a) ao Portal Bontech!",
            title=f"Sua conta foi criada com sucesso, {user.name}!",
            body_html=f"""
            <p>Seja muito bem-vindo(a) ao portal oficial da <strong>Bontech TI & Governança</strong>.</p>
            <p>Através da sua área do cliente, você pode solicitar diagnósticos e acompanhar em tempo real todas as suas propostas e consultorias em <strong>GLPi, Automação n8n, Gestão de Incidentes, Ativos (ITAM), Conhecimento (KCS) e Central de Serviços</strong>.</p>
            """,
        )

        setting = Setting.query.first()
        webhook_url = setting.n8n_webhook_url if setting else ""
        trigger_n8n_webhook(
            "user_registered",
            {
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "company": user.company,
                "provider": "local",
            },
            webhook_url=webhook_url,
        )

        flash("Cadastro realizado com sucesso! Bem-vindo(a) ao Portal Bontech.", "success")
        return redirect(url_for("client.dashboard"))

    return render_template("auth/register.html")


@auth_bp.route("/google")
def google_login():
    client_id = current_app.config.get("GOOGLE_CLIENT_ID")
    client_secret = current_app.config.get("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret or "seu_client_id" in client_id:
        flash(
            "O login social com Google requer a configuração das chaves GOOGLE_CLIENT_ID e GOOGLE_CLIENT_SECRET no arquivo .env.",
            "warning",
        )
        return redirect(url_for("auth.login"))

    redirect_uri = current_app.config.get("GOOGLE_CALLBACK_URL") or url_for(
        "auth.google_callback", _external=True
    )
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route("/google/callback")
def google_callback():
    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get("userinfo")
        if not user_info:
            user_info = oauth.google.userinfo()
    except Exception as exc:
        current_app.logger.error(f"Erro no callback Google OAuth: {exc}")
        flash("Não foi possível autenticar com o Google no momento. Tente novamente.", "danger")
        return redirect(url_for("auth.login"))

    email = (user_info.get("email") or "").strip().lower()
    google_id = user_info.get("sub")
    name = user_info.get("name") or email.split("@")[0]
    picture = user_info.get("picture")

    if not email:
        flash("Sua conta Google não forneceu um endereço de e-mail válido.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter(
        (User.google_id == google_id) | (User.email == email)
    ).first()

    if not user:
        user = User(
            name=name,
            email=email,
            google_id=google_id,
            avatar_url=picture,
            role="client",
            is_active_account=True,
        )
        db.session.add(user)
        db.session.flush()
    else:
        if not user.google_id:
            user.google_id = google_id
        if picture:
            user.avatar_url = picture

    if not user.is_active_account:
        flash("Sua conta está desativada. Entre em contato com o suporte.", "warning")
        return redirect(url_for("auth.login"))

    user.last_login = datetime.now(timezone.utc)
    _link_orphan_consultations(user)
    db.session.commit()

    login_user(user, remember=True)
    flash(f"Autenticado via Google com sucesso! Olá, {user.name}.", "success")

    if user.is_admin:
        return redirect(url_for("admin.dashboard"))
    return redirect(url_for("client.dashboard"))


@auth_bp.route("/esqueci-senha", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
            db.session.commit()

            base_url = current_app.config.get("BASE_URL", "https://bontech.com.br")
            reset_link = f"{base_url}/auth/redefinir-senha/{token}"
            send_email(
                to_email=user.email,
                subject="Redefinição de Senha — Bontech",
                title="Solicitação de Nova Senha",
                body_html=f"""
                <p>Olá, <strong>{user.name}</strong>.</p>
                <p>Recebemos uma solicitação para redefinir a senha da sua conta no portal da Bontech.</p>
                <p style="margin:24px 0;">
                  <a href="{reset_link}" style="background:#0052CC;color:#FFFFFF;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:700;">Redefinir Minha Senha</a>
                </p>
                <p style="font-size:13px;color:#64748B;">Este link é válido por 1 hora. Caso não tenha solicitado, basta ignorar este e-mail.</p>
                """,
            )
        flash(
            "Se o e-mail informado estiver cadastrado, enviamos as instruções de redefinição de senha.",
            "info",
        )
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html")


@auth_bp.route("/redefinir-senha/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    now = datetime.now(timezone.utc)
    if not user or not user.reset_token_expires or user.reset_token_expires < now:
        flash("O link de redefinição é inválido ou expirou. Solicite um novo.", "danger")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if len(password) < 6 or password != confirm:
            flash("Verifique se a senha possui no mínimo 6 caracteres e se a confirmação coincide.", "danger")
            return render_template("auth/reset_password.html", token=token)

        user.set_password(password)
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()
        flash("Sua senha foi atualizada com sucesso! Faça login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu da sua conta com segurança.", "info")
    return redirect(url_for("public.index"))
