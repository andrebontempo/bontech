import random
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models import ConsultationRequest, Service, Setting
from app.utils.mail import send_email, trigger_n8n_webhook

client_bp = Blueprint("client", __name__, url_prefix="/minha-conta")


@client_bp.route("")
@client_bp.route("/")
@login_required
def dashboard():
    # Vincula solicitações antigas com o mesmo e-mail caso existam
    orphans = ConsultationRequest.query.filter_by(
        email=current_user.email.lower(), user_id=None
    ).all()
    if orphans:
        for item in orphans:
            item.user_id = current_user.id
        db.session.commit()

    consultations = (
        ConsultationRequest.query.filter_by(user_id=current_user.id)
        .order_by(ConsultationRequest.created_at.desc())
        .all()
    )
    services = (
        Service.query.filter_by(is_active=True)
        .order_by(Service.display_order.asc())
        .all()
    )
    return render_template(
        "client/dashboard.html",
        consultations=consultations,
        services=services,
    )


@client_bp.route("/nova-solicitacao", methods=["POST"])
@login_required
def create_consultation():
    service_interest = request.form.get("service_interest", "Consultoria Geral em TI").strip()
    subject = request.form.get("subject", "").strip()
    message = request.form.get("message", "").strip()

    if not message:
        flash("Descreva a sua necessidade para abrir a solicitação.", "danger")
        return redirect(url_for("client.dashboard"))

    if not subject:
        subject = f"Solicitação de Consultoria — {service_interest}"

    now_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    protocol = f"BNT-{now_str}-{random.randint(1000, 9999)}"

    consultation = ConsultationRequest(
        protocol=protocol,
        name=current_user.name,
        email=current_user.email,
        phone=current_user.phone,
        company=current_user.company,
        service_interest=service_interest,
        subject=subject,
        message=message,
        status="Novo",
        user_id=current_user.id,
    )
    db.session.add(consultation)
    db.session.commit()

    setting = Setting.query.first()
    admin_email = (
        setting.contact_email
        if setting and setting.contact_email
        else current_app.config.get("ADMIN_ALERT_EMAIL", "suporte@bontech.com.br")
    )

    send_email(
        to_email=admin_email,
        subject=f"🔔 Nova Solicitação no Portal [{protocol}] — {current_user.name}",
        title="Nova Solicitação pelo Portal do Cliente",
        body_html=f"""
        <p>O cliente <strong>{current_user.name}</strong> ({current_user.email}) abriu uma nova solicitação no Portal Bontech:</p>
        <ul>
          <li><strong>Protocolo:</strong> {protocol}</li>
          <li><strong>Empresa:</strong> {current_user.company or 'Não informada'}</li>
          <li><strong>Serviço:</strong> {service_interest}</li>
          <li><strong>Assunto:</strong> {subject}</li>
        </ul>
        <p><strong>Descrição:</strong><br>{message}</p>
        """,
    )

    webhook_url = setting.n8n_webhook_url if setting else ""
    trigger_n8n_webhook(
        "consultation_created",
        {
            "protocol": protocol,
            "name": current_user.name,
            "email": current_user.email,
            "phone": current_user.phone,
            "company": current_user.company,
            "service_interest": service_interest,
            "subject": subject,
            "message": message,
        },
        webhook_url=webhook_url,
    )

    flash(f"Solicitação {protocol} registrada com sucesso!", "success")
    return redirect(url_for("client.dashboard"))


@client_bp.route("/perfil", methods=["POST"])
@login_required
def update_profile():
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    company = request.form.get("company", "").strip()
    new_password = request.form.get("new_password", "")

    if name:
        current_user.name = name
    current_user.phone = phone
    current_user.company = company

    if new_password:
        if len(new_password) < 6:
            flash("A nova senha deve possuir no mínimo 6 caracteres.", "danger")
            return redirect(url_for("client.dashboard"))
        current_user.set_password(new_password)

    db.session.commit()
    flash("Seus dados cadastrais foram atualizados com sucesso!", "success")
    return redirect(url_for("client.dashboard"))
