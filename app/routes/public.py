import random
from datetime import datetime, timezone
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    Response,
    current_app,
)
from flask_login import current_user
from sqlalchemy import or_
from app.extensions import db, limiter
from app.models import Service, Post, Category, ConsultationRequest, Setting
from app.utils.mail import send_email, trigger_n8n_webhook

public_bp = Blueprint("public", __name__)


def _generate_protocol() -> str:
    now_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    rand_num = random.randint(1000, 9999)
    return f"BNT-{now_str}-{rand_num}"


@public_bp.route("/")
def index():
    services = (
        Service.query.filter_by(is_active=True)
        .order_by(Service.display_order.asc(), Service.id.asc())
        .all()
    )
    recent_posts = (
        Post.query.filter_by(is_published=True)
        .order_by(Post.published_at.desc())
        .limit(3)
        .all()
    )
    return render_template(
        "public/index.html",
        services=services,
        recent_posts=recent_posts,
    )


@public_bp.route("/servicos")
def services_list():
    services = (
        Service.query.filter_by(is_active=True)
        .order_by(Service.display_order.asc(), Service.id.asc())
        .all()
    )
    return render_template("public/services.html", services=services)


@public_bp.route("/servicos/<slug>")
def service_detail(slug):
    service = Service.query.filter_by(slug=slug, is_active=True).first_or_404()
    other_services = (
        Service.query.filter(Service.id != service.id, Service.is_active.is_(True))
        .order_by(Service.display_order.asc())
        .all()
    )
    return render_template(
        "public/service_detail.html",
        service=service,
        other_services=other_services,
    )


@public_bp.route("/contato", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def contact():
    services = (
        Service.query.filter_by(is_active=True)
        .order_by(Service.display_order.asc())
        .all()
    )
    preselected_service = request.args.get("servico", "")

    if request.method == "POST":
        # Honeypot anti-bot
        if request.form.get("website_url"):
            flash("Sua solicitação foi recebida com sucesso!", "success")
            return redirect(url_for("public.contact"))

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        company = request.form.get("company", "").strip()
        service_interest = request.form.get(
            "service_interest", "Consultoria Geral em TI"
        ).strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not email or not message:
            flash("Por favor, preencha nome, e-mail e mensagem.", "danger")
            return render_template(
                "public/contact.html",
                services=services,
                preselected_service=service_interest,
            )

        if not subject:
            subject = f"Solicitação de Consultoria — {service_interest}"

        protocol = _generate_protocol()
        consultation = ConsultationRequest(
            protocol=protocol,
            name=name,
            email=email,
            phone=phone,
            company=company,
            service_interest=service_interest,
            subject=subject,
            message=message,
            status="Novo",
            user_id=current_user.id if current_user.is_authenticated else None,
        )
        db.session.add(consultation)
        db.session.commit()

        setting = Setting.query.first()
        admin_email = (
            setting.contact_email
            if setting and setting.contact_email
            else current_app.config.get("ADMIN_ALERT_EMAIL", "suporte@bontech.com.br")
        )

        # Notifica o cliente
        send_email(
            to_email=email,
            subject=f"[{protocol}] Recebemos sua solicitação — Bontech",
            title=f"Olá, {name}!",
            body_html=f"""
            <p>Recebemos sua solicitação de contato/consultoria na <strong>Bontech</strong>.</p>
            <p><strong>Protocolo de Atendimento:</strong> <span style="background:#EFF6FF;color:#0052CC;padding:4px 8px;border-radius:6px;font-weight:700;">{protocol}</span></p>
            <p><strong>Serviço de Interesse:</strong> {service_interest}</p>
            <p><strong>Resumo da Mensagem:</strong><br>{message}</p>
            <p>Nossa equipe de especialistas analisará sua demanda e retornará em breve. Você também pode acompanhar o andamento desta solicitação fazendo login com este mesmo e-mail em nosso portal.</p>
            """,
        )

        # Notifica o administrador
        send_email(
            to_email=admin_email,
            subject=f"🔔 Nova Solicitação [{protocol}] — {service_interest}",
            title="Nova Solicitação de Consultoria / Contato",
            body_html=f"""
            <p>Um novo lead entrou em contato pelo portal da <strong>Bontech</strong>:</p>
            <ul>
              <li><strong>Protocolo:</strong> {protocol}</li>
              <li><strong>Nome:</strong> {name}</li>
              <li><strong>E-mail:</strong> {email}</li>
              <li><strong>Telefone/WhatsApp:</strong> {phone or 'Não informado'}</li>
              <li><strong>Empresa:</strong> {company or 'Não informada'}</li>
              <li><strong>Serviço:</strong> {service_interest}</li>
              <li><strong>Assunto:</strong> {subject}</li>
            </ul>
            <p><strong>Mensagem:</strong><br>{message}</p>
            """,
        )

        # Dispara Webhook para o n8n se configurado
        webhook_url = setting.n8n_webhook_url if setting else ""
        trigger_n8n_webhook(
            "consultation_created",
            {
                "protocol": protocol,
                "name": name,
                "email": email,
                "phone": phone,
                "company": company,
                "service_interest": service_interest,
                "subject": subject,
                "message": message,
            },
            webhook_url=webhook_url,
        )

        flash(
            f"Solicitação enviada com sucesso! Seu protocolo é {protocol}. "
            "Acesse sua conta para acompanhar o status em tempo real.",
            "success",
        )
        if current_user.is_authenticated:
            return redirect(url_for("client.dashboard"))
        return redirect(url_for("public.contact"))

    return render_template(
        "public/contact.html",
        services=services,
        preselected_service=preselected_service,
    )


@public_bp.route("/politica-de-privacidade")
def privacy():
    return render_template("public/privacy.html")


@public_bp.route("/busca")
def search():
    q = request.args.get("q", "").strip()
    posts = []
    services = []
    if q:
        like_pattern = f"%{q}%"
        posts = (
            Post.query.filter(
                Post.is_published.is_(True),
                or_(
                    Post.title.ilike(like_pattern),
                    Post.summary.ilike(like_pattern),
                    Post.content.ilike(like_pattern),
                    Post.tags.ilike(like_pattern),
                ),
            )
            .order_by(Post.published_at.desc())
            .all()
        )
        services = (
            Service.query.filter(
                Service.is_active.is_(True),
                or_(
                    Service.title.ilike(like_pattern),
                    Service.short_description.ilike(like_pattern),
                    Service.full_description.ilike(like_pattern),
                ),
            )
            .order_by(Service.display_order.asc())
            .all()
        )
    return render_template("public/search.html", q=q, posts=posts, services=services)


@public_bp.route("/health")
def health():
    return jsonify({"status": "ok", "service": "bontech-flask"}), 200


@public_bp.route("/manifest.json")
def manifest():
    return jsonify(
        {
            "name": "Bontech — Help Desk, Automação n8n & Governança de TI",
            "short_name": "Bontech TI",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#0A1931",
            "theme_color": "#0052CC",
            "icons": [
                {
                    "src": "/static/img/favicon.svg",
                    "sizes": "any",
                    "type": "image/svg+xml",
                }
            ],
        }
    )


@public_bp.route("/robots.txt")
def robots():
    base_url = current_app.config.get("BASE_URL", "https://bontech.com.br")
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /minha-conta/",
        f"Sitemap: {base_url}/sitemap.xml",
    ]
    return Response("\n".join(lines), mimetype="text/plain")


@public_bp.route("/sitemap.xml")
def sitemap():
    base_url = current_app.config.get("BASE_URL", "https://bontech.com.br")
    services = Service.query.filter_by(is_active=True).all()
    posts = Post.query.filter_by(is_published=True).all()

    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    for path in ["", "/servicos", "/blog", "/contato", "/politica-de-privacidade"]:
        xml.append(f"  <url><loc>{base_url}{path}</loc></url>")

    for s in services:
        xml.append(f"  <url><loc>{base_url}/servicos/{s.slug}</loc></url>")

    for p in posts:
        xml.append(f"  <url><loc>{base_url}/blog/{p.slug}</loc></url>")

    xml.append("</urlset>")
    return Response("\n".join(xml), mimetype="application/xml")
