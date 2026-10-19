# 📋 PRD — Novo Portal Institucional & Blog Corporativo Bontech (Flask)

> **Status:** ✅ **APROVADO & DEFINIDO**
> **Objetivo:** Substituir integralmente o antigo site em WordPress (`bontech.com.br`) por uma aplicação web moderna, rápida, segura e modular em **Python (Flask)** com **PostgreSQL 16**, containerizada em **Docker** e com **CI/CD automatizado via GitHub Actions** (`/opt/docker/bontech`), alinhada ao padrão de excelência dos demais projetos do ecossistema (`vistabem`, `oqueeisso`, `inmemoriambrasil`, `chatiabontech`).

---

## ✅ 1. Decisões Consolidadas de Arquitetura & Escopo

1. **Banco de Dados:** **PostgreSQL 16 (`postgres:16-alpine`)** com `Flask-SQLAlchemy`, migrações e busca Full-Text em português para o Blog e Serviços.
2. **Infraestrutura & Rede Proxy na VPS:**
   - Diretório na VPS: `/opt/docker/bontech`
   - Container da Aplicação (`bontech-app`) na porta `80` conectado à rede externa `proxy` com os aliases: `bontech`, `bontech-app`, `bontech_wordpress`, `wordpress` e `bontech_nginx` (garantindo transição transparente no Nginx Proxy Manager sem necessidade de intervenção manual).
   - O `deploy.sh` executará `docker compose down --remove-orphans`, desativando os antigos containers `wordpress` e `mariadb` automaticamente.
3. **Autenticação & Portal do Cliente (Mini-CRM):**
   - **Login Local** (E-mail/Senha com `Werkzeug`/`bcrypt`, recuperação de senha por e-mail) + **Login Social Google OAuth 2.0** (`Authlib`).
   - **Área do Cliente (`/minha-conta`):** Clientes autenticados podem abrir e acompanhar o status de suas **Solicitações de Consultoria / Orçamento** (`Novo`, `Em Análise`, `Proposta Enviada`, `Em Andamento`, `Concluído`) e visualizar respostas/interações da equipe Bontech.
   - **Painel Administrativo (`/admin`):** Gestão completa de Serviços, Artigos do Blog (CMS com upload de imagens WebP), Solicitações/Leads (Mini-CRM com resposta ao cliente e atalho para WhatsApp), Usuários e **Modo de Manutenção Programada (HTTP 503 SEO-friendly)**.
4. **Seed Inicial Completo:**
   - O sistema já subirá povoado automaticamente com os **6 Serviços principais** da Bontech:
     1. **Plataforma de Help Desk & Central de Serviços (GLPi)**
     2. **Automação Inteligente em TI (n8n & Chatbots)**
     3. **Consultoria em Gestão de Incidentes e Requisições (ITSM)**
     4. **Gestão de Ativos de TI (ITAM) & Inventário**
     5. **Gestão do Conhecimento (KCS)**
     6. **Estruturação e Governança de Central de Serviços (CSC)**
   - E com os **artigos iniciais do Blog** (*"Automação descomplicada com n8n"*, *"Help Desk eficiente com GLPi"*, *"Gestão de Ativos de TI (ITAM): Controle e Redução de Custos"* e *"KCS na Prática: Transformando Conhecimento em Resolução Rápida"*).

---

## 🖼️ 2. Identidade Visual & Design System

Baseado no layout de referência fornecido, modernizado com CSS3 customizado, tipografia `Plus Jakarta Sans` / `Inter` e total responsividade (Mobile-First + PWA):

| Elemento | Cor / Token | Aplicação |
| :--- | :--- | :--- |
| **Azul Royal Corporativo (Primary)** | `#0052CC` / `#0066FF` | Botões de ação (CTAs), destaques de título (`Bontech`, `Serviços`, `Blog`), ícones e barra superior secundária. |
| **Azul Marinho Profundo (Dark Navy)** | `#0A1931` / `#0F2547` | Topbar principal, rodapé institucional e cabeçalhos. |
| **Fundo Escuro / Seções em Destaque** | `#0F172A` (Slate 900) | Hero section com overlay escuro sobre imagem corporativa e seção "Nossos Recursos / Pilares". |
| **Superfícies Claras** | `#FFFFFF` e `#F8FAFC` | Fundo de cards de Serviços, artigos do Blog e áreas de leitura limpa. |

---

## 📂 3. Estrutura do Projeto

```text
/home/andre/GitHub/bontech/
├── .github/
│   └── workflows/
│       └── deploy.yml          # Esteira CI/CD GitHub Actions (Validação Python + Deploy VPS)
├── app/
│   ├── __init__.py             # Application Factory do Flask, middlewares e context processors
│   ├── config.py               # Configurações via variáveis de ambiente (.env)
│   ├── extensions.py           # Instâncias SQLAlchemy, LoginManager, OAuth, Limiter, CSRF
│   ├── models.py               # Modelos PostgreSQL (User, Service, Post, Category, ConsultationRequest, Setting)
│   ├── seed.py                 # Povoamento automático dos 6 serviços, categorias, posts e admin
│   ├── utils/
│   │   ├── mail.py             # Disparo de e-mails HTML via SMTP (Hostinger)
│   │   └── media.py            # Processamento e conversão de uploads para WebP (Pillow)
│   ├── routes/
│   │   ├── public.py           # Home, Serviços, Detalhe do Serviço, Contato, Política de Privacidade, Sitemap/SEO
│   │   ├── blog.py             # Listagem do Blog, Categorias, Busca Full-Text e Leitura de Artigo
│   │   ├── auth.py             # Login Local, Cadastro, Recuperação de Senha e Google OAuth 2.0
│   │   ├── client.py           # Portal do Cliente (/minha-conta) para acompanhar solicitações de consultoria
│   │   └── admin.py            # Painel Administrativo (/admin) - Dashboard, CMS Blog, Serviços, Leads e Manutenção 503
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css       # Design System completo inspirado na referência visual
│   │   ├── js/
│   │   │   └── main.js         # Interações, modal de busca, alertas e PWA
│   │   ├── img/                # Imagens institucionais e capas geradas para os serviços/artigos
│   │   └── uploads/            # Volume persistente de arquivos enviados pelo painel
│   └── templates/
│       ├── base.html           # Layout mestre (Topbar, Navbar, Footer azul marinho, Modal de Busca)
│       ├── public/             # Home, Detalhe de Serviço, Contato, Privacidade, Manutenção 503
│       ├── blog/               # Index do Blog e Leitura do Artigo
│       ├── auth/               # Login, Cadastro, Esqueci a Senha, Redefinir Senha
│       ├── client/             # Painel do Cliente (Minhas Solicitações de Consultoria)
│       └── admin/              # Dashboard, Gerenciar Posts, Serviços, Solicitações e Configurações
├── deploy.sh                   # Script de deploy automatizado na VPS
├── docker-compose.yml          # Orquestração bontech-app (Flask/Gunicorn) + bontech-db (Postgres 16)
├── Dockerfile                  # Imagem Python 3.12 Slim otimizada
├── .env.example                # Modelo de variáveis de ambiente
├── requirements.txt            # Dependências Python
├── DOCUMENTACAO.md             # Documentação técnica e operacional completa
├── PRD.md                      # Este documento de requisitos
└── wsgi.py                     # Ponto de entrada Gunicorn / Flask
```
