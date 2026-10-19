# 🚀 Bontech — Portal Corporativo, Blog & Governança de TI (Flask)

Aplicação web moderna em **Python (Flask)** e **PostgreSQL 16** para a **Bontech (`bontech.com.br`)**, oferecendo:
- **Home Page & Portfólio de Serviços:** Help Desk em GLPi, Automação em n8n, Consultoria em Gestão de Incidentes, Ativos (ITAM), Conhecimento (KCS) e Central de Serviços (CSC).
- **Blog Corporativo & Base de Conhecimento:** Artigos em Markdown com filtro por categorias, tempo de leitura e busca textual.
- **Autenticação Híbrida:** Login Local (E-mail/Senha) + Login Social via **Google OAuth 2.0**.
- **Portal do Cliente (`/minha-conta`):** Acompanhamento de solicitações de orçamento e consultoria por protocolo.
- **Painel Administrativo (`/admin`):** Gestão completa de Leads/Solicitações (Mini-CRM), Serviços, Blog (com conversão automática de imagens para WebP), Usuários e Modo de Manutenção HTTP 503.

## 🐳 Como Executar com Docker Compose

```bash
cp .env.example .env
docker network create proxy 2>/dev/null || true
docker compose up -d --build
```

Acesse localmente em `http://localhost:5015` (ou via Nginx Proxy Manager na rede `proxy`).
