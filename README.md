# Sistema de Eleição CIPA 2026

Aplicação web desenvolvida em Flask para gerenciar o processo eleitoral da CIPA (Comissão Interna de Prevenção de Acidentes) da Neoenergia Brasília. Suporta múltiplas unidades com controle de candidatos, funcionários e votação em tempo real.

---

## Índice

1. [O que o sistema faz](#o-que-o-sistema-faz)
2. [Requisitos](#requisitos)
3. [Instalação e execução local](#instalação-e-execução-local)
4. [Variáveis de ambiente](#variáveis-de-ambiente)
5. [Banco de dados](#banco-de-dados)
6. [Estrutura de pastas](#estrutura-de-pastas)
7. [Módulos principais](#módulos-principais)
8. [Testes automatizados](#testes-automatizados)
9. [Deploy (Railway)](#deploy-railway)
10. [Melhorias futuras](#melhorias-futuras)

---

## O que o sistema faz

O sistema possui duas áreas distintas:

**Área pública** — acessível por qualquer funcionário:
- Página inicial com informações da eleição
- Login por matrícula e unidade para votar
- Tela de votação com lista de candidatos e fotos
- Confirmação de voto registrado

**Painel administrativo** (`/admin`) — restrito ao administrador:
- Gerenciar candidatos (cadastrar, editar, remover, upload de foto)
- Gerenciar funcionários (cadastrar, remover, pesquisar, filtrar, paginar)
- Abrir e fechar eleições por unidade ou todas ao mesmo tempo
- Acompanhar participação em tempo real
- Visualizar resultado parcial ou final com ranking de votos
- Finalizar eleição e salvar resultado no histórico
- Consultar histórico de eleições anteriores

**Unidades suportadas:** UTD Sobradinho, UTD Planaltina, UTD SIA, Sede Park Shopping, UTD Taguatinga, UTD Lago Sul, UTD São Sebastião.

---

## Requisitos

- Python 3.10 ou superior
- pip

Dependências Python (ver `requirements.txt`):

| Pacote | Versão | Uso |
|---|---|---|
| Flask | 3.0.0 | Framework web |
| Flask-SQLAlchemy | 3.1.1 | ORM para banco de dados |
| Werkzeug | 3.0.1 | Hashing de senhas, upload de arquivos |
| Gunicorn | 21.2.0 | Servidor WSGI para produção |
| pytest | 8.3.5 | Framework de testes |
| pytest-cov | 6.1.0 | Relatório de cobertura de testes |

---

## Instalação e execução local

### 1. Clonar o repositório

```bash
git clone <url-do-repositorio>
cd Projeto-Cipa-2026
```

### 2. Criar e ativar ambiente virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python -m venv venv
source venv/bin/activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente (opcional para desenvolvimento)

Crie um arquivo `.env` na raiz ou exporte manualmente (ver seção [Variáveis de ambiente](#variáveis-de-ambiente)). Para rodar localmente sem configuração extra, os valores padrão já funcionam.

### 5. Rodar a aplicação

```bash
python run.py
```

A aplicação estará disponível em `http://localhost:5000`.

**Credenciais padrão do admin:**
- Usuário: `admin`
- Senha: `cipa2026`

> O banco de dados e o usuário admin são criados automaticamente na primeira execução.

---

## Variáveis de ambiente

| Variável | Padrão (desenvolvimento) | Descrição |
|---|---|---|
| `SECRET_KEY` | `cipa2026_chave_secreta` | Chave de criptografia das sessões Flask. **Deve ser trocada em produção.** |
| `DATABASE_URL` | `sqlite:///cipa.db` | URI do banco de dados. Em produção, usar PostgreSQL (ex: `postgresql://user:pass@host/db`). |

> Em produção, nunca use os valores padrão. Configure essas variáveis diretamente no painel do provedor de hospedagem.

---

## Banco de dados

### Tecnologia

Em desenvolvimento: **SQLite** (arquivo `instance/cipa.db`, criado automaticamente).  
Em produção: recomenda-se **PostgreSQL** via variável `DATABASE_URL`.

### Modelos (tabelas)

| Modelo | Tabela | Descrição |
|---|---|---|
| `Admin` | `admin` | Usuário administrador com senha em hash |
| `Candidato` | `candidato` | Candidatos por unidade com foto (caminho do arquivo) |
| `Funcionario` | `funcionario` | Funcionários habilitados a votar, com flag `votou` |
| `Voto` | `voto` | Cada voto registrado, vinculado a um candidato |
| `Eleicao` | `eleicao` | Status da eleição por unidade (`aberta` / `fechada`) |
| `HistoricoEleicao` | `historico_eleicao` | Snapshot JSON de resultados finalizados |

### Inicialização

O banco é criado automaticamente ao iniciar a aplicação (`create_app` chama `_init_db()`). Não há sistema de migrations — qualquer alteração de schema exige recriar o banco manualmente em desenvolvimento, ou gerenciar via SQL em produção.

### Fotos de candidatos

Fotos são salvas em `static/uploads/` com nome UUID (`<uuid>.jpg`). O banco armazena apenas o caminho relativo (`/static/uploads/<uuid>.jpg`). O limite de upload é **5 MB** por arquivo. Formatos aceitos: `jpg`, `jpeg`, `png`, `gif`.

> **Atenção (produção):** plataformas como Railway têm sistema de arquivos efêmero — os uploads são perdidos a cada redeploy. Para persistência, integrar com um serviço de armazenamento externo (ex: AWS S3, Cloudflare R2).

---

## Estrutura de pastas

```
Projeto-Cipa-2026/
│
├── run.py                  # Ponto de entrada da aplicação
├── config.py               # Classes de configuração (Dev / Prod)
├── requirements.txt        # Dependências Python
├── pytest.ini              # Configuração do pytest
├── Procfile                # Comando de start para Heroku-compatíveis
├── railway.toml            # Configuração de deploy no Railway
│
├── app/                    # Pacote principal da aplicação
│   ├── __init__.py         # Application factory (create_app)
│   ├── extensions.py       # Instância do SQLAlchemy (db)
│   ├── models.py           # Modelos ORM (tabelas do banco)
│   ├── constants.py        # Listas fixas: UNIDADES, ALLOWED_EXTENSIONS
│   ├── utils.py            # Decorador login_required
│   │
│   ├── routes/
│   │   ├── admin/          # Blueprint 'admin' — prefixo /admin
│   │   │   ├── auth.py         # Login e logout
│   │   │   ├── dashboard.py    # Painel principal
│   │   │   ├── candidatos.py   # CRUD de candidatos
│   │   │   ├── funcionarios.py # CRUD de funcionários + filtros + paginação
│   │   │   ├── eleicao.py      # Abrir / fechar eleições
│   │   │   ├── participacao.py # Acompanhamento em tempo real
│   │   │   ├── resultado.py    # Resultado e finalização
│   │   │   └── historico.py    # Histórico de eleições passadas
│   │   │
│   │   └── public/         # Blueprint 'public' — sem prefixo
│   │       └── votacao.py      # Fluxo público: home, login, votar, confirmação
│   │
│   └── services/
│       └── foto.py         # Salvar, deletar e migrar fotos de candidatos
│
├── templates/              # Templates Jinja2
│   ├── base.html               # Layout base público
│   ├── base_admin.html         # Layout base administrativo (sidebar + navbar)
│   ├── home.html               # Página inicial pública
│   ├── login_admin.html        # Tela de login do admin
│   ├── admin/
│   │   ├── _macros.html        # Macro de paginação reutilizável
│   │   ├── dashboard.html
│   │   ├── candidatos.html
│   │   ├── funcionarios.html
│   │   ├── eleicao.html
│   │   ├── participacao.html
│   │   ├── resultado.html
│   │   ├── historico.html
│   │   └── historico_detalhe.html
│   └── votacao/
│       ├── login.html          # Login do funcionário para votar
│       ├── votar.html          # Tela de escolha do candidato
│       └── confirmacao.html    # Confirmação de voto registrado
│
├── static/
│   ├── style.css               # Estilos globais
│   ├── logo-neoenergia.png
│   ├── fotos/                  # Imagens estáticas da aplicação
│   └── uploads/                # Fotos de candidatos (geradas em runtime)
│
├── tests/
│   ├── conftest.py             # Fixtures compartilhadas (app, db, client, domínio)
│   ├── test_auth.py            # Testes de autenticação do admin
│   ├── test_eleicao.py         # Testes de abertura/fechamento de eleições
│   ├── test_funcionarios.py    # Testes de CRUD de funcionários
│   └── test_votacao.py         # Testes do fluxo de votação e resultado
│
└── instance/
    └── cipa.db                 # Banco SQLite (gerado automaticamente, não versionar)
```

---

## Módulos principais

### `app/__init__.py` — Application Factory

Função `create_app(config_class)` que instancia o Flask, registra os Blueprints e inicializa o banco. Aceita uma classe de configuração como argumento, o que permite injetar configurações diferentes em testes (ex: banco em memória).

### `app/models.py` — Modelos do banco

Define todas as tabelas via SQLAlchemy ORM. O relacionamento `Candidato → Voto` usa `cascade='all, delete-orphan'`, garantindo que os votos de um candidato sejam removidos automaticamente se o candidato for deletado.

### `app/routes/admin/` — Blueprint administrativo

Cada arquivo corresponde a uma área funcional. Todas as rotas são protegidas pelo decorador `@login_required` (exceto `auth.py`). A paginação em `funcionarios.py` e `candidatos.py` usa o método `.paginate()` do SQLAlchemy, com filtros passados via query string (GET params), tornando as URLs filtradas compartilháveis.

### `app/routes/public/votacao.py` — Fluxo de votação

Controle de estado via `session['funcionario_id']`. O sistema valida matrícula, unidade, status da eleição e flag `votou` antes de permitir o acesso à tela de voto. Após o voto, a sessão é limpa e o funcionário não consegue votar novamente.

### `app/services/foto.py` — Gerenciamento de fotos

Três funções independentes:
- `salvar_foto(file)` — valida extensão, gera nome UUID, salva e retorna o caminho
- `deletar_foto(url)` — remove o arquivo físico a partir do caminho armazenado no banco
- `migrar_base64(candidato)` — converte fotos legadas em base64 para arquivo físico

### `tests/conftest.py` — Infraestrutura de testes

Usa `StaticPool` do SQLAlchemy para compartilhar a mesma conexão SQLite em memória entre a fixture e os requests HTTP do cliente de teste. O `app context` é mantido explicitamente via `ctx.push()/ctx.pop()`. O flag `TESTING=True` impede que o `_init_db()` de produção seja executado durante os testes.

---

## Testes automatizados

### Rodar todos os testes

```bash
pytest
```

### Rodar com relatório de cobertura

```bash
pytest --cov=app --cov-report=term-missing
```

### Rodar apenas um módulo

```bash
pytest tests/test_votacao.py -v
```

### Organização

| Arquivo | Cobertura |
|---|---|
| `test_auth.py` | Login com sucesso/falha, proteção de rotas, logout |
| `test_eleicao.py` | Abrir/fechar individual e em massa, rota inválida (404) |
| `test_funcionarios.py` | Cadastro, matrícula duplicada, remoção, acesso não autenticado |
| `test_votacao.py` | Voto válido, duplicado, eleição fechada, matrícula inválida, resultado |
| `test_candidatos.py` | Cadastro, rejeição sem nome/unidade, listagem, remoção, acesso não autenticado |
| `test_historico.py` | Listagem, detalhe, vencedor por unidade, exclusão, rotas inexistentes (404), acesso não autenticado |

### Estratégia de isolamento

Cada teste recebe um banco limpo (criado e descartado pela fixture `db`). Não há dependência de estado entre testes. Dados mínimos (admin + 7 eleições fechadas) são semeados automaticamente antes de cada teste.

---

## Deploy (Railway)

O projeto está configurado para deploy automático no [Railway](https://railway.app).

### Arquivos de configuração

- **`Procfile`**: `web: gunicorn run:app --bind 0.0.0.0:$PORT`
- **`railway.toml`**: define builder Nixpacks, comando de start e healthcheck em `/`

### Variáveis obrigatórias no painel do Railway

| Variável | Valor |
|---|---|
| `SECRET_KEY` | String aleatória longa (ex: gerada com `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `DATABASE_URL` | URI do banco PostgreSQL provisionado pelo Railway |

### Limitações conhecidas

- **Uploads de fotos não persistem** entre deploys por causa do sistema de arquivos efêmero do Railway. Para resolver, integrar `app/services/foto.py` com AWS S3 ou serviço equivalente.
- **Sem migrations automáticas**: alterações no schema exigem recriar o banco ou executar SQL manualmente.

---

## Melhorias futuras

### Infraestrutura
- [ ] Integrar Flask-Migrate (Alembic) para gerenciar alterações de schema sem perda de dados
- [ ] Substituir upload local por armazenamento em nuvem (AWS S3, Cloudflare R2)
- [ ] Adicionar variável `FLASK_ENV` para selecionar config automaticamente (`DevelopmentConfig` / `ProductionConfig`)

### Segurança
- [ ] Adicionar rate limiting no login do admin e no login de votação para prevenir força bruta
- [ ] Implementar CSRF protection via Flask-WTF (atualmente desabilitado nos testes via `WTF_CSRF_ENABLED=False`)
- [ ] Expirar sessão de votação automaticamente após tempo limite

### Funcionalidades
- [ ] Permitir múltiplos administradores com níveis de acesso diferentes
- [ ] Exportar resultado em PDF ou Excel diretamente pelo painel
- [ ] Notificação por e-mail quando uma eleição for aberta
- [ ] Modo de votação anônima auditável (dissociar voto do funcionário sem perder contagem)
- [ ] Dashboard com gráficos de participação em tempo real

### Qualidade
- [x] Aumentar cobertura de testes para incluir candidatos e histórico
- [ ] Adicionar testes de integração end-to-end (ex: Playwright ou Selenium)
- [ ] Configurar CI/CD com GitHub Actions para rodar testes a cada push

---

## Autor

Desenvolvido para a Neoenergia Brasília — Processo Eleitoral CIPA 2026.
