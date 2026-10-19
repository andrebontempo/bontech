from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


def utc_now():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    """Modelo de Usuário com suporte a autenticação Local e Google OAuth 2.0."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=True)
    google_id = db.Column(db.String(120), unique=True, nullable=True, index=True)
    avatar_url = db.Column(db.String(500), nullable=True)
    phone = db.Column(db.String(40), nullable=True)
    company = db.Column(db.String(150), nullable=True)
    role = db.Column(db.String(20), nullable=False, default="client")  # 'admin' ou 'client'
    is_active_account = db.Column(db.Boolean, default=True, nullable=False)
    reset_token = db.Column(db.String(128), nullable=True, index=True)
    reset_token_expires = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    last_login = db.Column(db.DateTime(timezone=True), nullable=True)

    posts = db.relationship("Post", backref="author", lazy="dynamic")
    consultations = db.relationship(
        "ConsultationRequest", backref="client", lazy="dynamic"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


class Service(db.Model):
    """Serviços e Soluções de TI oferecidos pela Bontech."""

    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    slug = db.Column(db.String(160), unique=True, nullable=False, index=True)
    badge = db.Column(db.String(80), nullable=True)
    short_description = db.Column(db.String(320), nullable=False)
    full_description = db.Column(db.Text, nullable=False)
    features_list = db.Column(db.Text, nullable=True)  # Itens separados por quebra de linha
    benefits_list = db.Column(db.Text, nullable=True)  # Benefícios separados por quebra de linha
    icon_name = db.Column(db.String(60), nullable=False, default="headset")
    cover_image = db.Column(db.String(300), nullable=True)
    display_order = db.Column(db.Integer, default=1, nullable=False)
    is_featured = db.Column(db.Boolean, default=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    @property
    def features(self):
        if not self.features_list:
            return []
        return [line.strip() for line in self.features_list.splitlines() if line.strip()]

    @property
    def benefits(self):
        if not self.benefits_list:
            return []
        return [line.strip() for line in self.benefits_list.splitlines() if line.strip()]


class Category(db.Model):
    """Categorias do Blog e Base de Conhecimento (KCS)."""

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.String(250), nullable=True)
    posts = db.relationship("Post", backref="category", lazy="dynamic")


class Post(db.Model):
    """Artigos do Blog Corporativo e Publicações Técnicas."""

    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    summary = db.Column(db.String(400), nullable=False)
    content = db.Column(db.Text, nullable=False)
    cover_image = db.Column(db.String(300), nullable=True)
    tags = db.Column(db.String(250), nullable=True)
    reading_time = db.Column(db.Integer, default=4, nullable=False)
    views = db.Column(db.Integer, default=0, nullable=False)
    is_published = db.Column(db.Boolean, default=True, nullable=False)
    published_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    category_id = db.Column(
        db.Integer, db.ForeignKey("categories.id"), nullable=True, index=True
    )
    author_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True, index=True
    )

    @property
    def tag_list(self):
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(",") if t.strip()]


class ConsultationRequest(db.Model):
    """Solicitações de Consultoria, Diagnóstico e Contato (Mini-CRM / Portal do Cliente)."""

    __tablename__ = "consultation_requests"

    id = db.Column(db.Integer, primary_key=True)
    protocol = db.Column(db.String(30), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), nullable=False, index=True)
    phone = db.Column(db.String(40), nullable=True)
    company = db.Column(db.String(150), nullable=True)
    service_interest = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(
        db.String(40), nullable=False, default="Novo"
    )  # Novo, Em Análise, Proposta Enviada, Em Andamento, Concluído
    admin_response = db.Column(db.Text, nullable=True)
    responded_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)


class Setting(db.Model):
    """Configurações globais do portal e Modo de Manutenção Programada (503 SEO)."""

    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(120), default="Bontech")
    site_tagline = db.Column(
        db.String(200), default="Help Desk e Automações em TI"
    )
    hero_badge = db.Column(
        db.String(160), default="BONTECH! Provendo governança para o seu negócio"
    )
    hero_title = db.Column(
        db.String(220),
        default="Amplie as possibilidades do seu negócio com a Bontech",
    )
    hero_subtitle = db.Column(
        db.String(350),
        default="Uma plataforma de Help Desk completa, Automação inteligente em n8n e Consultoria especializada em Governança de TI (ITSM, GLPi, Ativos e KCS).",
    )
    contact_email = db.Column(db.String(150), default="suporte@bontech.com.br")
    contact_phone = db.Column(db.String(50), default="+55 61 98427-4022")
    whatsapp_number = db.Column(db.String(30), default="5561984274022")
    address = db.Column(db.String(200), default="Brasília, DF 70299-120")
    opening_hours = db.Column(db.String(120), default="Seg-Sex: 08h às 18h | Suporte 24/7")
    instagram_url = db.Column(db.String(250), default="https://instagram.com/bontech")
    linkedin_url = db.Column(db.String(250), default="https://linkedin.com/company/bontech")
    youtube_url = db.Column(db.String(250), default="")
    n8n_webhook_url = db.Column(db.String(350), default="")

    # Modo de Manutenção Programada (SEO 503)
    maintenance_mode = db.Column(db.Boolean, default=False, nullable=False)
    maintenance_title = db.Column(
        db.String(160), default="Estamos atualizando nossa plataforma de Governança"
    )
    maintenance_message = db.Column(
        db.Text,
        default="Realizamos melhorias programadas em nossos sistemas para oferecer uma experiência ainda mais rápida e segura. Voltaremos em instantes.",
    )
    maintenance_eta = db.Column(db.String(100), default="Em breve")
    updated_at = db.Column(
        db.DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
