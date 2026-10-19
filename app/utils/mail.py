import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from flask import current_app


def _send_smtp_async(app, to_email: str, subject: str, html_body: str):
    """Envia e-mail HTML em background via SMTP."""
    with app.app_context():
        smtp_host = app.config.get("SMTP_HOST")
        smtp_port = app.config.get("SMTP_PORT", 465)
        smtp_user = app.config.get("SMTP_USER")
        smtp_pass = app.config.get("SMTP_PASS")
        from_name = app.config.get("SMTP_FROM_NAME", "Bontech TI & Governança")

        if not smtp_host or not smtp_user or not smtp_pass:
            app.logger.info(
                f"[SMTP Simulado] Para: {to_email} | Assunto: {subject}"
            )
            return

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{from_name} <{smtp_user}>"
            msg["To"] = to_email
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            if smtp_port == 465:
                with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as server:
                    server.login(smtp_user, smtp_pass)
                    server.sendmail(smtp_user, [to_email], msg.as_string())
            else:
                with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.sendmail(smtp_user, [to_email], msg.as_string())
        except Exception as exc:
            app.logger.warning(f"Falha ao enviar e-mail SMTP para {to_email}: {exc}")


def send_email(to_email: str, subject: str, title: str, body_html: str):
    """Formata e dispara e-mail corporativo com a identidade visual Bontech."""
    app = current_app._get_current_object()
    base_url = app.config.get("BASE_URL", "https://bontech.com.br")

    template = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head><meta charset="UTF-8"></head>
    <body style="margin:0;padding:0;background-color:#F1F5F9;font-family:'Segoe UI',Arial,sans-serif;color:#1E293B;">
      <table width="100%" cellpadding="0" cellspacing="0" style="padding:32px 16px;">
        <tr>
          <td align="center">
            <table width="600" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(10,25,49,0.08);">
              <tr>
                <td style="background:linear-gradient(135deg,#0A1931 0%,#0052CC 100%);padding:28px 32px;color:#FFFFFF;">
                  <h1 style="margin:0;font-size:24px;font-weight:800;letter-spacing:-0.5px;">Bontech</h1>
                  <p style="margin:4px 0 0;font-size:13px;opacity:0.85;">Help Desk, Automação em n8n & Governança de TI</p>
                </td>
              </tr>
              <tr>
                <td style="padding:32px;">
                  <h2 style="margin-top:0;color:#0A1931;font-size:20px;">{title}</h2>
                  <div style="font-size:15px;line-height:1.6;color:#334155;">
                    {body_html}
                  </div>
                </td>
              </tr>
              <tr>
                <td style="background:#0A1931;padding:20px 32px;text-align:center;color:#94A3B8;font-size:12px;">
                  <p style="margin:0;">© 2026 Bontech — Brasília, DF | <a href="{base_url}" style="color:#38BDF8;text-decoration:none;">bontech.com.br</a></p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """
    thread = threading.Thread(
        target=_send_smtp_async, args=(app, to_email, subject, template), daemon=True
    )
    thread.start()


def trigger_n8n_webhook(event_type: str, payload: dict, webhook_url: str = ""):
    """Dispara evento JSON assíncrono para o n8n caso haja URL configurada."""
    url = webhook_url or current_app.config.get("N8N_WEBHOOK_URL", "")
    if not url:
        return

    def _post():
        try:
            requests.post(
                url,
                json={"event": event_type, "data": payload},
                timeout=10,
            )
        except Exception:
            pass

    threading.Thread(target=_post, daemon=True).start()
