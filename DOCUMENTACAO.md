# 📘 Documentação Técnica & Operacional — Portal Bontech (Flask)

> Portal corporativo, blog técnico (KCS), área do cliente (Mini-CRM de solicitações de consultoria) e painel administrativo da **Bontech TI & Governança**, desenvolvido em **Python 3.12 (Flask)**, **PostgreSQL 16**, **Docker Compose** e **CI/CD automatizado via GitHub Actions** — substituindo integralmente a antiga instalação em WordPress.

---

## 🏗️ 1. Arquitetura do Sistema & Stack Tecnológica

| Camada | Tecnologia Utilizada | Descrição |
| :--- | :--- | :--- |
| **Backend** | Python 3.12 + Flask 3.0 + Gunicorn | Arquitetura modular com Blueprints (`public`, `blog`, `auth`, `client`, `admin`). |
| **Banco de Dados** | PostgreSQL 16 Alpine + SQLAlchemy | Persistência relacional de alta performance e baixo consumo de RAM (~40 MB). |
| **Autenticação** | Flask-Login + Authlib (Google OAuth 2.0) | Login tradicional (E-mail/Senha com hash seguro) e Login Social Google. |
| **Segurança** | Flask-WTF (CSRF) + Flask-Limiter + Honeypot | Proteção contra ataques CSRF, força bruta e bots em formulários. |
| **Mídia & Conteúdo** | Pillow (WebP) + Python-Markdown | Conversão automática de uploads de imagem para WebP e artigos em Markdown. |
| **Notificações** | SMTP (Hostinger) + Webhook n8n | Disparo assíncrono de e-mails HTML corporativos e integração JSON com n8n. |
| **Infraestrutura** | Docker Compose + Nginx Proxy Manager | Conectado à rede externa `proxy` com todos os aliases de transição do antigo WordPress. |

---

## 🎯 2. Portfólio de Serviços (Seed Inicial Automático)

Ao subir pela primeira vez, o script `app/seed.py` popula automaticamente:
1. **Plataforma de Help Desk (GLPi)** — Implantação, catálogo de serviços, SLA e dashboards.
2. **Automação em TI com n8n** — Workflows, chatbots no WhatsApp, integrações REST e agentes de IA.
3. **Consultoria em Gestão de Incidentes** — Processos ITIL, matriz de prioridade, MTTR e Major Incidents.
4. **Gestão de Ativos de TI (ITAM)** — Inventário automatizado (GLPi Agent), CMDB e controle de licenças.
5. **Gestão do Conhecimento (KCS)** — Metodologia KCS v6, templates padronizados e portal de FAQ.
6. **Consultoria em Central de Serviços (CSC)** — Governança, ESM (TI, RH, Financeiro) e indicadores (CSAT/KPIs).

Além disso, cria as categorias e os artigos técnicos iniciais do **Nosso Blog**.

---

## 🔐 3. Autenticação Local & Google OAuth 2.0

### Configuração no Google Cloud Console:
1. Acesse o **[Google Cloud Console](https://console.cloud.google.com/)**.
2. Em **APIs e Serviços > Credenciais**, crie ou selecione um **ID do cliente OAuth 2.0** (*Aplicativo da Web*).
3. Em **Origens JavaScript autorizadas**, adicione:
   - `https://bontech.com.br`
4. Em **URIs de redirecionamento autorizados**, adicione:
   - `https://bontech.com.br/auth/google/callback`
5. Preencha `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET` no arquivo `.env` na VPS (`/opt/docker/bontech/.env`).

---

## 🛠️ 4. Modo de Manutenção Programada (HTTP 503 SEO Friendly)

- **Ativação com 1 clique:** Em **Painel Admin (`/admin?tab=configuracoes`)**, marque a opção **Ativar Modo de Manutenção Programada** e clique em salvar.
- **Preservação de SEO:** Visitantes e crawlers recebem status **HTTP 503 (Service Unavailable)** com cabeçalho `Retry-After: 3600` e meta tag `noindex, nofollow, noarchive`.
- **Bypass de Administrador:** Administradores logados continuam navegando normalmente por todo o portal com um banner de aviso no topo.

---

## 🐳 5. Deploy Automatizado (CI/CD GitHub Actions)

Seguindo a regra global, **nenhuma conexão SSH manual é feita na VPS**. O deploy ocorre automaticamente a cada `git push origin main`:
1. O workflow `.github/workflows/deploy.yml` valida e compila todos os pacotes Python (`python -m compileall app wsgi.py`).
2. Aciona `/opt/docker/bontech/deploy.sh` na VPS.
3. O `deploy.sh` executa `docker compose down --remove-orphans` (removendo os antigos containers `wordpress` e `mariadb`) e sobe `bontech-app` e `bontech-db` com `docker compose up -d --build --remove-orphans`.
