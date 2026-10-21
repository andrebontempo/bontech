from datetime import datetime, timezone
from functools import wraps
import os
import markdown
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models import User, Service, Category, Post, ConsultationRequest, Setting
from app.utils.media import slugify, save_image_as_webp
from app.utils.mail import send_email

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash("Acesso restrito a administradores da Bontech.", "danger")
            return redirect(url_for("public.index"))
        return f(*args, **kwargs)

    return decorated_function


def _load_internal_docs() -> dict:
    """Lê e converte os documentos técnicos internos (Markdown -> HTML) exclusivamente para o Admin."""
    project_root = os.path.abspath(os.path.join(current_app.root_path, ".."))
    docs_map = {
        "arquitetura": ("VISAO_GERAL_ESTRUTURA.md", "Arquitetura & Estrutura de Código"),
        "operacional": ("DOCUMENTACAO.md", "Documentação Técnica & Operacional"),
        "prd": ("PRD.md", "PRD — Requisitos do Produto"),
    }
    result = {}
    for key, (filename, label) in docs_map.items():
        filepath = os.path.join(project_root, filename)
        raw_md = ""
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                raw_md = f.read()
        html = markdown.markdown(
            raw_md or f"*Arquivo `{filename}` não encontrado.*",
            extensions=["extra", "fenced_code", "tables", "nl2br"],
        )
        result[key] = {"label": label, "filename": filename, "html": html}
    return result


@admin_bp.route("")
@admin_bp.route("/")
@admin_required
def dashboard():
    tab = request.args.get("tab", "visao-geral")
    doc_key = request.args.get("doc", "arquitetura")
    services = Service.query.order_by(Service.display_order.asc(), Service.id.asc()).all()
    posts = Post.query.order_by(Post.published_at.desc()).all()
    categories = Category.query.order_by(Category.name.asc()).all()
    consultations = ConsultationRequest.query.order_by(
        ConsultationRequest.created_at.desc()
    ).all()
    users = User.query.order_by(User.created_at.desc()).all()
    setting = Setting.query.first()

    stats = {
        "total_services": len(services),
        "total_posts": len(posts),
        "total_views": sum((p.views or 0) for p in posts),
        "total_consultations": len(consultations),
        "open_consultations": sum(
            1 for c in consultations if c.status in ("Novo", "Em Análise")
        ),
        "total_users": len(users),
    }

    internal_docs = _load_internal_docs() if tab == "documentacao" else {}
    if doc_key not in internal_docs and internal_docs:
        doc_key = "arquitetura"

    return render_template(
        "admin/dashboard.html",
        tab=tab,
        doc_key=doc_key,
        internal_docs=internal_docs,
        stats=stats,
        services=services,
        posts=posts,
        categories=categories,
        consultations=consultations,
        users=users,
        setting=setting,
    )


# ----------------------------------------------------------------------------
# Gestão de Solicitações / Leads (Mini-CRM)
# ----------------------------------------------------------------------------
@admin_bp.route("/solicitacoes/<int:req_id>/responder", methods=["POST"])
@admin_required
def respond_consultation(req_id):
    consultation = ConsultationRequest.query.get_or_404(req_id)
    new_status = request.form.get("status", consultation.status).strip()
    admin_response = request.form.get("admin_response", "").strip()

    consultation.status = new_status
    if admin_response:
        consultation.admin_response = admin_response
        consultation.responded_at = datetime.now(timezone.utc)

    db.session.commit()

    # Notifica o cliente por e-mail
    send_email(
        to_email=consultation.email,
        subject=f"[{consultation.protocol}] Atualização na sua solicitação ({new_status}) — Bontech",
        title=f"Atualização na Solicitação {consultation.protocol}",
        body_html=f"""
        <p>Olá, <strong>{consultation.name}</strong>.</p>
        <p>Sua solicitação referente a <strong>{consultation.service_interest}</strong> teve o status atualizado para:
           <span style="background:#EFF6FF;color:#0052CC;padding:4px 10px;border-radius:6px;font-weight:700;">{new_status}</span>
        </p>
        {f'<div style="background:#F8FAFC;border-left:4px solid #0052CC;padding:16px;margin:16px 0;"><strong>Parecer da Equipe Bontech:</strong><br>{admin_response}</div>' if admin_response else ''}
        <p>Você pode acompanhar todos os detalhes acessando sua área do cliente em nosso site.</p>
        """,
    )

    flash(f"Solicitação {consultation.protocol} atualizada e cliente notificado!", "success")
    return redirect(url_for("admin.dashboard", tab="solicitacoes"))


@admin_bp.route("/solicitacoes/<int:req_id>/excluir", methods=["POST"])
@admin_required
def delete_consultation(req_id):
    consultation = ConsultationRequest.query.get_or_404(req_id)
    db.session.delete(consultation)
    db.session.commit()
    flash("Solicitação removida com sucesso.", "info")
    return redirect(url_for("admin.dashboard", tab="solicitacoes"))


# ----------------------------------------------------------------------------
# Gestão de Serviços
# ----------------------------------------------------------------------------
@admin_bp.route("/servicos/salvar", methods=["POST"])
@admin_required
def save_service():
    service_id = request.form.get("service_id")
    title = request.form.get("title", "").strip()
    badge = request.form.get("badge", "").strip()
    short_description = request.form.get("short_description", "").strip()
    full_description = request.form.get("full_description", "").strip()
    features_list = request.form.get("features_list", "").strip()
    benefits_list = request.form.get("benefits_list", "").strip()
    icon_name = request.form.get("icon_name", "headset").strip()
    display_order = int(request.form.get("display_order") or 1)
    is_active = bool(request.form.get("is_active"))

    if not title or not short_description:
        flash("Preencha o título e o resumo do serviço.", "danger")
        return redirect(url_for("admin.dashboard", tab="servicos"))

    if service_id:
        service = Service.query.get_or_404(int(service_id))
    else:
        slug = slugify(title)
        if Service.query.filter_by(slug=slug).first():
            slug = f"{slug}-{int(datetime.now(timezone.utc).timestamp())}"
        service = Service(slug=slug)
        db.session.add(service)

    service.title = title
    service.badge = badge
    service.short_description = short_description
    service.full_description = full_description or short_description
    service.features_list = features_list
    service.benefits_list = benefits_list
    service.icon_name = icon_name
    service.display_order = display_order
    service.is_active = is_active

    uploaded = request.files.get("cover_image")
    if uploaded and uploaded.filename:
        webp_path = save_image_as_webp(uploaded, prefix="service")
        if webp_path:
            service.cover_image = webp_path
    elif not service.cover_image:
        service.cover_image = "/static/img/service-glpi.svg"

    db.session.commit()
    flash(f"Serviço '{service.title}' salvo com sucesso!", "success")
    return redirect(url_for("admin.dashboard", tab="servicos"))


@admin_bp.route("/servicos/<int:service_id>/excluir", methods=["POST"])
@admin_required
def delete_service(service_id):
    service = Service.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()
    flash("Serviço removido com sucesso.", "info")
    return redirect(url_for("admin.dashboard", tab="servicos"))


# ----------------------------------------------------------------------------
# Gestão do Blog (Posts & Categorias)
# ----------------------------------------------------------------------------
@admin_bp.route("/blog/salvar", methods=["POST"])
@admin_required
def save_post():
    post_id = request.form.get("post_id")
    title = request.form.get("title", "").strip()
    summary = request.form.get("summary", "").strip()
    content = request.form.get("content", "").strip()
    tags = request.form.get("tags", "").strip()
    category_id = request.form.get("category_id")
    reading_time = int(request.form.get("reading_time") or 4)
    is_published = bool(request.form.get("is_published"))

    if not title or not summary or not content:
        flash("Preencha título, resumo e conteúdo do artigo.", "danger")
        return redirect(url_for("admin.dashboard", tab="blog"))

    if post_id:
        post = Post.query.get_or_404(int(post_id))
    else:
        slug = slugify(title)
        if Post.query.filter_by(slug=slug).first():
            slug = f"{slug}-{int(datetime.now(timezone.utc).timestamp())}"
        post = Post(slug=slug, author_id=current_user.id)
        db.session.add(post)

    post.title = title
    post.summary = summary
    post.content = content
    post.tags = tags
    post.reading_time = reading_time
    post.is_published = is_published
    if category_id:
        post.category_id = int(category_id)

    uploaded = request.files.get("cover_image")
    if uploaded and uploaded.filename:
        webp_path = save_image_as_webp(uploaded, prefix="blog")
        if webp_path:
            post.cover_image = webp_path
    elif not post.cover_image:
        post.cover_image = "/static/img/blog-glpi.svg"

    db.session.commit()
    flash(f"Artigo '{post.title}' salvo com sucesso!", "success")
    return redirect(url_for("admin.dashboard", tab="blog"))


@admin_bp.route("/blog/<int:post_id>/excluir", methods=["POST"])
@admin_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash("Artigo excluído com sucesso.", "info")
    return redirect(url_for("admin.dashboard", tab="blog"))


@admin_bp.route("/categorias/salvar", methods=["POST"])
@admin_required
def save_category():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    if name:
        slug = slugify(name)
        if not Category.query.filter_by(slug=slug).first():
            db.session.add(Category(name=name, slug=slug, description=description))
            db.session.commit()
            flash(f"Categoria '{name}' criada!", "success")
    return redirect(url_for("admin.dashboard", tab="blog"))


# ----------------------------------------------------------------------------
# Gestão de Usuários
# ----------------------------------------------------------------------------
@admin_bp.route("/usuarios/<int:user_id>/papel", methods=["POST"])
@admin_required
def toggle_user_role(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("Você não pode alterar seu próprio nível de acesso.", "warning")
        return redirect(url_for("admin.dashboard", tab="usuarios"))

    new_role = request.form.get("role", "client")
    if new_role in ("admin", "client"):
        user.role = new_role
        db.session.commit()
        flash(f"Nível de acesso de {user.name} atualizado para {new_role}.", "success")
    return redirect(url_for("admin.dashboard", tab="usuarios"))


@admin_bp.route("/usuarios/<int:user_id>/senha", methods=["POST"])
@admin_required
def reset_user_password(user_id):
    user = User.query.get_or_404(user_id)
    new_password = request.form.get("new_password", "").strip()

    if not new_password or len(new_password) < 6:
        flash("A nova senha deve possuir no mínimo 6 caracteres.", "danger")
        return redirect(url_for("admin.dashboard", tab="usuarios"))

    user.set_password(new_password)
    db.session.commit()
    flash(f"Senha de {user.name} ({user.email}) atualizada com sucesso!", "success")
    return redirect(url_for("admin.dashboard", tab="usuarios"))


# ----------------------------------------------------------------------------
# Configurações Gerais & Modo de Manutenção Programada (SEO 503)
# ----------------------------------------------------------------------------
@admin_bp.route("/configuracoes/salvar", methods=["POST"])
@admin_required
def save_settings():
    setting = Setting.query.first()
    if not setting:
        setting = Setting()
        db.session.add(setting)

    setting.site_name = request.form.get("site_name", "Bontech").strip()
    setting.site_tagline = request.form.get("site_tagline", "").strip()
    setting.hero_badge = request.form.get("hero_badge", "").strip()
    setting.hero_title = request.form.get("hero_title", "").strip()
    setting.hero_subtitle = request.form.get("hero_subtitle", "").strip()
    setting.contact_email = request.form.get("contact_email", "").strip()
    setting.contact_phone = request.form.get("contact_phone", "").strip()
    setting.whatsapp_number = request.form.get("whatsapp_number", "").strip()
    setting.address = request.form.get("address", "").strip()
    setting.opening_hours = request.form.get("opening_hours", "").strip()
    setting.instagram_url = request.form.get("instagram_url", "").strip()
    setting.linkedin_url = request.form.get("linkedin_url", "").strip()
    setting.n8n_webhook_url = request.form.get("n8n_webhook_url", "").strip()

    setting.maintenance_mode = bool(request.form.get("maintenance_mode"))
    setting.maintenance_title = request.form.get("maintenance_title", "").strip()
    setting.maintenance_message = request.form.get("maintenance_message", "").strip()
    setting.maintenance_eta = request.form.get("maintenance_eta", "").strip()

    db.session.commit()
    flash("Configurações gerais e modo de manutenção atualizados com sucesso!", "success")
    return redirect(url_for("admin.dashboard", tab="configuracoes"))
