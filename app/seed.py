from flask import current_app
from app.extensions import db
from app.models import User, Service, Category, Post, Setting


def run_seed():
    """Popula o banco PostgreSQL inicial com Configurações, Admin, 6 Serviços e Artigos do Blog."""
    # 1. Configurações Globais
    setting = Setting.query.first()
    if not setting:
        setting = Setting(
            site_name="Bontech",
            site_tagline="Help Desk e Automações em TI",
            hero_badge="BONTECH! Provendo governança para o seu negócio",
            hero_title="Amplie as possibilidades do seu negócio com a Bontech",
            hero_subtitle="Uma plataforma de Help Desk completa baseada em GLPi, automação inteligente de processos com n8n e consultoria especializada em Governança de TI (Incidentes, Ativos, Conhecimento e Central de Serviços).",
            contact_email="suporte@bontech.com.br",
            contact_phone="+55 61 98427-4022",
            whatsapp_number="5561984274022",
            address="Brasília, DF 70299-120",
            opening_hours="Seg-Sáb: 08h às 18h | Suporte 24/7",
            n8n_webhook_url=current_app.config.get("N8N_WEBHOOK_URL", ""),
            maintenance_mode=False,
        )
        db.session.add(setting)

    # 2. Administrador Inicial
    admin_email = current_app.config.get("ADMIN_EMAIL", "suporte@bontech.com.br").lower()
    admin_user = User.query.filter_by(email=admin_email).first()
    if not admin_user:
        admin_user = User(
            name=current_app.config.get("ADMIN_NAME", "Humberto Bontempo"),
            email=admin_email,
            phone="+55 61 98427-4022",
            company="Bontech TI & Governança",
            role="admin",
            is_active_account=True,
        )
        admin_user.set_password(current_app.config.get("ADMIN_PASSWORD", "Bontech@2026"))
        db.session.add(admin_user)
        db.session.flush()
    elif admin_user.name == "André Bontempo":
        admin_user.name = "Humberto Bontempo"
        db.session.flush()

    # 3. Portfólio Completo dos 6 Serviços de TI da Bontech
    if Service.query.count() == 0:
        services_data = [
            {
                "title": "Plataforma de Help Desk (GLPi)",
                "slug": "plataforma-de-help-desk-glpi",
                "badge": "ITSM & GLPi",
                "short_description": "Plataforma baseada no GLPi para registro, monitoramento, SLA e contabilização completa de chamados e serviços de TI.",
                "full_description": """A **Bontech** implanta, customiza e gerencia ambientes completos de **Service Desk e Help Desk baseados no GLPi**, a solução open source líder mundial em Gestão de Serviços de TI (ITSM).

Transformamos o atendimento da sua equipe técnica com um portal de autoatendimento intuitivo, catálogo de serviços estruturado por áreas de negócio, acordos de nível de serviço (SLA/OLA) automatizados e painéis gerenciais em tempo real.

Seja para estruturar sua operação do zero ou migrar de ferramentas legadas de alto custo, entregamos uma plataforma robusta, integrada ao Active Directory/LDAP, com notificações inteligentes por e-mail e WhatsApp.""",
                "features_list": """Implantação e customização avançada do GLPi 10+
Catálogo de Serviços estruturado com formulários dinâmicos
Gestão de SLA (Tempo de Primeira Resposta e Tempo de Solução)
Autenticação Single Sign-On (LDAP / Active Directory / OAuth)
Notificações multicanal (E-mail e integração WhatsApp via n8n)
Dashboards gerenciais de produtividade e volumetria""",
                "benefits_list": """Redução de até 45% no tempo médio de atendimento (TMA)
Eliminação de custos com licenças por atendente
Rastreabilidade total de cada demanda da abertura ao fechamento
Visibilidade executiva sobre gargalos e desempenho da equipe""",
                "icon_name": "headset",
                "cover_image": "/static/img/service-glpi.svg",
                "display_order": 1,
                "is_featured": True,
            },
            {
                "title": "Automação em TI com n8n",
                "slug": "automacao-em-ti-n8n",
                "badge": "Workflows & IA",
                "short_description": "Serviço de Automação e Integração em TI usando a plataforma n8n, WhatsApp, APIs corporativas e chatbots inteligentes.",
                "full_description": """Potencialize a eficiência operacional da sua empresa eliminando tarefas manuais e repetitivas através da **Automação de Workflows com n8n**.

Desenvolvemos fluxos de integração sob medida que conectam seu **GLPi, ERPs, CRMs, bancos de dados, sistemas de monitoramento (Zabbix/Prometheus), WhatsApp e agentes de Inteligência Artificial**.

Automatizamos desde a triagem e abertura de chamados via chatbot no WhatsApp até o provisionamento de acessos, disparo de alertas críticos em tempo real e sincronização de cadastros entre sistemas.""",
                "features_list": """Arquitetura e implantação dedicada de servidores n8n
Chatbots de triagem e abertura de chamados via WhatsApp
Integração bidirecional via API REST e Webhooks com GLPi e ERPs
Agentes de IA para classificação automática de incidentes e resumo de tickets
Automação de onboarding/offboarding de colaboradores e acessos
Monitoramento ativo com alertas inteligentes no WhatsApp e Telegram""",
                "benefits_list": """Operação 24/7 sem intervenção humana em rotinas padronizadas
Redução drástica de erros operacionais e retrabalho
Integração rápida entre sistemas que antes não conversavam
Retorno sobre investimento (ROI) imediato em horas técnicas economizadas""",
                "icon_name": "workflow",
                "cover_image": "/static/img/service-n8n.svg",
                "display_order": 2,
                "is_featured": True,
            },
            {
                "title": "Consultoria em Gestão de Incidentes",
                "slug": "consultoria-gestao-de-incidentes",
                "badge": "Continuidade & ITIL",
                "short_description": "Estruturação de processos de Gestão de Incidentes e Problemas alinhados ao ITIL para restauração rápida de serviços críticos.",
                "full_description": """Paradas não planejadas custam caro e comprometem a reputação do negócio. Nossa **Consultoria em Gestão de Incidentes** estrutura fluxos ágeis de detecção, classificação, escalonamento e resolução de falhas.

Mapeamos matrizes de prioridade (Impacto x Urgência), definimos fluxos claros de escalonamento funcional e hierárquico, implementamos rituais de **Major Incidents (Incidentes Críticos)** e conectamos o monitoramento de infraestrutura diretamente à fila de resposta da equipe.""",
                "features_list": """Desenho do processo de Gestão de Incidentes e Requisições (ITIL 4)
Matriz de Priorização (Impacto x Urgência) e definição de SLAs reais
Fluxo de resposta a Incidentes Críticos (Major Incident Management)
Integração de ferramentas de monitoramento (Zabbix) para abertura automática
Análise de Causa Raiz (RCA) e transição para Gestão de Problemas
Treinamento prático para analistas de Nível 1, Nível 2 e Especialistas""",
                "benefits_list": """Redução expressiva do MTTR (Tempo Médio para Reparo)
Fim dos chamados perdidos ou sem dono definido
Comunicação transparente com os usuários e áreas de negócio durante crises
Prevenção de recorrência de falhas através de gestão proativa""",
                "icon_name": "shield-alert",
                "cover_image": "/static/img/service-incidentes.svg",
                "display_order": 3,
                "is_featured": True,
            },
            {
                "title": "Gestão de Ativos de TI (ITAM)",
                "slug": "gestao-de-ativos-de-ti-itam",
                "badge": "Inventário & Licenças",
                "short_description": "Controle completo do ciclo de vida de hardware, software e licenças com inventário automatizado e conformidade.",
                "full_description": """Você sabe exatamente quantos computadores, servidores, monitores e licenças de software sua organização possui hoje, com quem estão e quando vencem as garantias?

Com a **Consultoria em Gestão de Ativos de TI (ITAM)** da Bontech, implementamos a descoberta e o inventário automatizado de todo o seu parque tecnológico integrado à CMDB do GLPi / TOPdesk, garantindo visibilidade financeira, controle de termos de responsabilidade e conformidade em auditorias de software.""",
                "features_list": """Inventário automatizado de Hardware e Software com agentes (GLPi Agent)
Estruturação de CMDB (Configuration Management Database)
Controle de Ciclo de Vida: Aquisição, Alocação, Manutenção e Descarte
Gestão de Licenciamento de Software e conformidade (Compliance)
Termos de responsabilidade digitais e rastreamento por centro de custo
Vinculação direta entre o ativo inventariado e o histórico de incidentes""",
                "benefits_list": """Eliminação de compras desnecessárias e licenças ociosas
Auditoria instantânea de configurações de estações e servidores
Planejamento orçamentário preciso para renovação de parque (Refresh)
Segurança patrimonial e redução de extravios de equipamentos""",
                "icon_name": "cpu",
                "cover_image": "/static/img/service-ativos.svg",
                "display_order": 4,
                "is_featured": True,
            },
            {
                "title": "Gestão do Conhecimento (KCS)",
                "slug": "gestao-do-conhecimento-kcs",
                "badge": "Base KCS & Autoatendimento",
                "short_description": "Implementação da metodologia KCS (Knowledge-Centered Service) para capturar, estruturar e reutilizar o conhecimento da equipe.",
                "full_description": """O conhecimento técnico da sua operação não pode ficar restrito à cabeça de poucos especialistas. Aplicamos a metodologia internacional **KCS (Knowledge-Centered Service)** para transformar a resolução diária de chamados em uma Base de Conhecimento viva, padronizada e pesquisável.

Criamos templates estruturados de artigos técnicos, fluxos de revisão editorial, portais de FAQ para usuários finais e integração com IA para sugerir soluções automaticamente antes mesmo da abertura do chamado.""",
                "features_list": """Arquitetura Corporativa de Gestão do Conhecimento (Metodologia KCS v6)
Padronização de templates de artigos (Sintoma, Ambiente, Causa e Resolução)
Portal de Autoatendimento (FAQ) para reduzir abertura de chamados simples
Fluxo de curadoria, ciclo de aprovação e indicadores de reuso de artigos
Capacitação da equipe técnica para documentar enquanto resolve
Integração de base de conhecimento com assistentes de IA""",
                "benefits_list": """Aumento da taxa de resolução no primeiro contato (FCR - First Call Resolution)
Aceleração do treinamento de novos analistas na equipe
Redução de até 30% no volume de chamados repetitivos (Nível 0 / Autoatendimento)
Preservação do capital intelectual da organização""",
                "icon_name": "book-open",
                "cover_image": "/static/img/service-kcs.svg",
                "display_order": 5,
                "is_featured": True,
            },
            {
                "title": "Consultoria em Central de Serviços (CSC)",
                "slug": "consultoria-central-de-servicos-csc",
                "badge": "Governança & CSC",
                "short_description": "Desenho, implantação e governança de Centrais de Serviços Compartilhados (TI, RH, Financeiro e Facilities) com foco em eficiência.",
                "full_description": """A **Bontech** apoia organizações públicas e privadas na estruturação e modernização de sua **Central de Serviços (Service Desk / CSC)**, unificando o atendimento de TI e áreas de negócios (RH, Administrativo, Compras, Facilities) em uma única plataforma governada.

Realizamos o diagnóstico de maturidade, redesenho do catálogo de serviços, definição de KPIs estratégicos, pesquisa de satisfação (CSAT/NPS) e acompanhamento executivo contínuo.""",
                "features_list": """Diagnóstico de maturidade operacional e redesenho da Central de Serviços
Expansão ESM (Enterprise Service Management) para RH, Financeiro e Facilities
Modelagem de Catálogo de Serviços Corporativo e Acordos de Nível de Serviço
Implementação de pesquisas de satisfação (CSAT) e indicadores executivos
Desenho de topologia de atendimento (N1, N2, N3) e dimensionamento de equipe
Acompanhamento de governança e melhoria contínua (CSI)""",
                "benefits_list": """Visão unificada da demanda de serviços em toda a organização
Padronização do atendimento e aumento da satisfação do usuário interno
Decisões baseadas em dados reais de capacidade, custo e desempenho
Maturidade de governança pronta para auditorias e certificações""",
                "icon_name": "layers",
                "cover_image": "/static/img/service-csc.svg",
                "display_order": 6,
                "is_featured": True,
            },
        ]

        for item in services_data:
            db.session.add(Service(**item))

    # 4. Categorias e Artigos Iniciais do Blog (preservando os temas do WordPress + novos)
    if Category.query.count() == 0:
        cat_helpdesk = Category(
            name="Help Desk & GLPi",
            slug="help-desk",
            description="Melhores práticas em GLPi, Central de Serviços e atendimento ao usuário.",
        )
        cat_automacao = Category(
            name="Automação & n8n",
            slug="automacao",
            description="Workflows inteligentes, integrações de APIs, chatbots e n8n em TI.",
        )
        cat_governanca = Category(
            name="Governança, ITAM & KCS",
            slug="governanca-ti",
            description="Gestão de Incidentes, Ativos de TI (ITAM) e Gestão do Conhecimento (KCS).",
        )
        db.session.add_all([cat_helpdesk, cat_automacao, cat_governanca])
        db.session.flush()

        posts_data = [
            {
                "title": "Automação descomplicada com n8n: potencialize seus processos de TI",
                "slug": "automacao-descomplicada-com-n8n",
                "summary": "Automatizar tarefas repetitivas é essencial para ganhar tempo e reduzir erros. Descubra como o n8n permite conectar sistemas, APIs, GLPi e WhatsApp de forma visual e segura.",
                "content": """## Por que automatizar a operação de TI com o n8n?

Automatizar tarefas repetitivas é essencial para ganhar tempo, reduzir falhas humanas e liberar a equipe técnica para projetos estratégicos. O **n8n** é uma plataforma *fair-code* poderosa de automação de workflows que permite conectar sistemas corporativos, APIs REST, bancos de dados e ferramentas de comunicação com total controle sobre os seus dados.

Na **Bontech**, utilizamos o n8n como o verdadeiro maestro de integrações para ambientes de TI e Centrais de Serviços:

### 1. Integração nativa entre GLPi e WhatsApp
Quantas vezes um usuário demora para ver um e-mail de atualização de chamado ou um analista perde um alerta de SLA prestes a vencer? Com fluxos automatizados no n8n:
- O usuário pode abrir chamados e consultar o protocolo diretamente pelo **WhatsApp**.
- Analistas recebem alertas instantâneos quando um incidente crítico (*Prioridade Alta/Urgente*) entra na fila.
- Pesquisas de satisfação são disparadas automaticamente após o encerramento do atendimento.

### 2. Onboarding e Offboarding de Colaboradores
A entrada ou saída de um colaborador exige dezenas de passos no Active Directory, criação de e-mail, alocação de equipamento no inventário e liberação de sistemas. Um único workflow no n8n orquestra todas essas etapas em segundos a partir da solicitação aprovada no catálogo de serviços.

### 3. Monitoramento Proativo + Inteligência Artificial
Ao conectar ferramentas como **Zabbix** ou **Prometheus** ao n8n, alertas de indisponibilidade são enriquecidos por modelos de IA (LLMs), que já anexam ao chamado no GLPi o diagnóstico preliminar e o artigo correspondente da Base de Conhecimento (KCS).

> **Quer implementar automações reais na sua operação de TI?** Solicite um diagnóstico com os especialistas da Bontech e descubra quais processos da sua empresa podem rodar no piloto automático.""",
                "cover_image": "/static/img/blog-n8n.svg",
                "tags": "n8n, Automação, API, WhatsApp, Workflows",
                "reading_time": 4,
                "views": 142,
                "category_id": cat_automacao.id,
                "author_id": admin_user.id,
            },
            {
                "title": "Help Desk eficiente com GLPi: governança e visibilidade de ponta a ponta",
                "slug": "help-desk-eficiente-com-glpi",
                "summary": "Oferecer um suporte ágil e organizado é essencial para manter a produtividade e a satisfação dos usuários. Veja como o GLPi transforma o gerenciamento de chamados e ativos.",
                "content": """## O papel estratégico do Help Desk na produtividade corporativa

Oferecer um suporte ágil, rastreável e organizado é essencial para manter a produtividade da organização e a satisfação dos usuários. O **GLPi (Gestionnaire Libre de Parc Informatique)** consolidou-se mundialmente como uma das soluções mais completas para **Gerenciamento de Serviços de TI (ITSM)** e **Inventário de Ativos (ITAM)**.

### O que diferencia uma implantação profissional do GLPi?

Muitas empresas instalam o GLPi com as configurações padrão e utilizam menos de 20% da capacidade da ferramenta. Na consultoria especializada da **Bontech**, estruturamos o GLPi para refletir a governança do seu negócio:

1. **Catálogo de Serviços Inteligente:** Substituímos campos de texto livre genéricos por formulários dinâmicos orientados ao serviço. O chamado já chega para a equipe certa com todas as informações necessárias.
2. **Gestão Real de SLA e OLA:** Calendários de horário comercial, feriados, pausas automáticas quando o chamado aguarda retorno do solicitante e escalonamento preventivo antes do estourar do prazo.
3. **Inventário Automatizado (GLPi Agent):** Cada computador ou servidor vinculado ao chamado exibe automaticamente seu processador, memória, softwares instalados e histórico de manutenções anteriores.
4. **Métricas Executivas:** Dashboards claros com volume de chamados por categoria, taxa de cumprimento de SLA, satisfação do usuário e desempenho por grupo solucionador.

Com o GLPi bem parametrizado, sua TI deixa de "apagar incêndios" no escuro e passa a operar com indicadores sólidos de nível de serviço.""",
                "cover_image": "/static/img/blog-glpi.svg",
                "tags": "GLPi, Help Desk, Service Desk, SLA, ITSM",
                "reading_time": 5,
                "views": 218,
                "category_id": cat_helpdesk.id,
                "author_id": admin_user.id,
            },
            {
                "title": "Gestão do Conhecimento (KCS) e Ativos (ITAM): os pilares invisíveis da TI de alta performance",
                "slug": "gestao-do-conhecimento-kcs-e-ativos-itam",
                "summary": "Descubra como unir um inventário de ativos preciso (ITAM) a uma base de conhecimento estruturada (KCS) reduz custos de licenciamento e acelera a resolução em primeiro nível.",
                "content": """## Por que Incidentes demoram para ser resolvidos?

Quando analisamos operações de suporte que sofrem com filas altas e lentidão no atendimento, quase sempre encontramos dois sintomas claros:
1. O analista **não tem visibilidade imediata sobre o ativo** (qual equipamento o usuário utiliza, versão do sistema operacional, alterações recentes).
2. Soluções para problemas recorrentes **não estão documentadas de forma padronizada**, obrigando cada técnico a "reinventar a roda" a cada novo chamado.

### A Sinergia entre ITAM e KCS

Na metodologia de consultoria da **Bontech**, tratamos a **Gestão de Ativos (ITAM)** e a **Gestão do Conhecimento (KCS)** como aceleradores diretos da Central de Serviços:

- **Com o ITAM estruturado:** Sabemos exatamente o ciclo de vida de cada estação de trabalho, notebook e servidor, controlamos garantias, evitamos compras desnecessárias e vinculamos incidentes recorrentes aos ativos problemáticos.
- **Com o KCS na rotina do Service Desk:** Cada incidente inédito gera ou aprimora um artigo estruturado (*Sintoma, Ambiente, Causa e Resolução Passo a Passo*). Na próxima ocorrência, qualquer analista de Nível 1 — ou o próprio usuário no portal de autoatendimento — resolve a demanda em minutos.

Essa combinação eleva drasticamente a resolução no primeiro contato (**FCR**) e constrói uma maturidade operacional sustentável para toda a empresa.""",
                "cover_image": "/static/img/blog-kcs.svg",
                "tags": "KCS, ITAM, Gestão de Ativos, Base de Conhecimento, Governança",
                "reading_time": 5,
                "views": 96,
                "category_id": cat_governanca.id,
                "author_id": admin_user.id,
            },
        ]

        for p_data in posts_data:
            db.session.add(Post(**p_data))

    db.session.commit()
