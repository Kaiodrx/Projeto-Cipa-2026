# CLAUDE.md

Este arquivo fornece orientações ao Claude Code (claude.ai/code) ao trabalhar com o código deste repositório.

## Orientações
Sempre me explique tudo o que está fazendo como se eu tivesse 15 anos de idade. Sou um profissional não técnico e quero aprender sobre tudo o que estamos fazendo.

## Comandos

```bash
# Instalar dependências
pip install -r requirements.txt

# Rodar o servidor de desenvolvimento
python run.py

# Rodar todos os testes
pytest

# Rodar um arquivo de teste específico
pytest tests/test_votacao.py

# Rodar um teste específico pelo nome
pytest tests/test_votacao.py::test_voto_duplicado -v

# Rodar testes com cobertura
pytest --cov=app
```

## Arquitetura

Aplicação Flask usando o padrão **application factory** (`app/__init__.py → create_app()`). As rotas são divididas em dois blueprints:

- **`app/routes/admin/`** — registrado em `/admin`, protegido por `@login_required` (sessão, admin único)
- **`app/routes/public/`** — sem prefixo, cuida do fluxo de votação do funcionário

O fluxo de votação usa `session['funcionario_id']` para manter estado entre as etapas: login do funcionário (`/votacao`) → seleção de candidato (`/votar`) → confirmação (`/confirmacao`).

### Banco de dados

SQLAlchemy com SQLite (desenvolvimento) e PostgreSQL (produção via variável `DATABASE_URL`). `_init_db()` em `app/__init__.py` roda na inicialização: cria as tabelas, cria o admin padrão (`admin`/`cipa2026`) e uma linha de `Eleicao` por unidade. É idempotente — os ALTER TABLE são envolvidos em try/except para não destruir dados existentes.

Modelos: `Admin`, `Candidato`, `Funcionario`, `Voto`, `Eleicao`, `HistoricoEleicao`.

Os resultados da eleição são arquivados como snapshots JSON em `HistoricoEleicao.dados` (não em tabelas normalizadas), preservando o estado exato no momento da finalização.

### Unidades

8 unidades fixas definidas em `app/constants.py` (`UNIDADES`):
- UTD SOBRADINHO, UTD PLANALTINA, UTD SIA, SEDE PARK SHOPPING
- UTD TAGUATINGA, UTD LAGO SUL, UTD SÃO SEBASTIÃO, UTD GAMA

Cada unidade tem sua própria linha em `Eleicao` com `status = 'aberta' | 'fechada'`. As eleições podem ser abertas/fechadas por unidade ou todas de uma vez.

### Rotas administrativas (`app/routes/admin/`)

| Arquivo | Responsabilidade |
|---|---|
| `auth.py` | Login e logout do admin |
| `dashboard.py` | Painel principal com status das eleições |
| `eleicao.py` | Abrir/fechar eleições por unidade ou todas |
| `candidatos.py` | CRUD de candidatos + upload de foto + vínculo com funcionário |
| `funcionarios.py` | CRUD de funcionários + importação via Excel |
| `apuracao.py` | Apuração detalhada por unidade com ranking e desempate |
| `relatorios.py` | 8 tipos de relatório (ver seção abaixo) |
| `participacao.py` | Acompanhamento em tempo real da participação na votação |
| `resultado.py` | Resultado geral + finalização da eleição |
| `historico.py` | Consulta e visualização de eleições passadas |

### Serviços (`app/services/`)

Lógica de negócio isolada das rotas, fácil de testar individualmente:

- **`dimensionamento.py`** — Calcula o número de titulares e suplentes pela Tabela I da NR-5 (Grau de Risco 3). Entrada: quantidade de funcionários. Suporta 13 faixas predefinidas + escalonamento acima de 10.000.
- **`apuracao.py`** — Apura os votos por unidade. Ordena candidatos por: votos (desc) → data de admissão (asc) → nome (asc). Marca situações de empate.
- **`foto.py`** — Upload de fotos com nome UUID, validação de extensão, deleção, migração de base64.

### Modelos de dados (`app/models.py`)

| Modelo | Finalidade | Campos principais |
|---|---|---|
| `Admin` | Credenciais do administrador | id, username, password (hash) |
| `Funcionario` | Eleitores aptos | id, matricula (único), nome, unidade, votou, ativo, data_admissao, data_nascimento, setor, cargo |
| `Candidato` | Candidatos à eleição | id, nome, cargo, unidade, foto (URL), funcionario_id (FK para desempate) |
| `Voto` | Votos registrados | id, candidato_id (FK), funcionario_id (FK), data_hora |
| `Eleicao` | Status por unidade | id, unidade, status, data_abertura, data_encerramento |
| `HistoricoEleicao` | Snapshots de eleições encerradas | id, titulo, data, dados (JSON) |

### Relatórios (`app/routes/admin/relatorios.py`)

8 relatórios, todos otimizados para impressão direta pelo navegador (`@media print`):

| Relatório | Conteúdo |
|---|---|
| Zerésima | Candidatos com zero votos (pré-eleição) |
| Boletim | Resumo da cédula com participação |
| Cartaz | Pôster visual dos eleitos (formato cartaz) |
| Eleitos | Lista de titulares e suplentes eleitos |
| Classificação | Ranking completo com status final |
| Votantes | Quem votou com horário |
| Não-votantes | Quem não votou |
| Eleitores | Cadastro completo do eleitorado |

### Upload de fotos

Fotos dos candidatos salvas em `static/uploads/` com nomes UUID. `app/services/foto.py` gerencia salvar/deletar. **Atenção:** no Railway (filesystem efêmero), as fotos são perdidas a cada redeploy — seria necessário integrar armazenamento em nuvem (S3/R2) para resolver isso.

### Importação de funcionários

Rota em `app/routes/admin/funcionarios.py` aceita planilha Excel (`.xlsx`) via `openpyxl`. Cria ou atualiza funcionários pelos campos: matrícula, nome, unidade, setor, cargo, data de admissão, data de nascimento.

### Testes

`tests/conftest.py` usa SQLite em memória com `StaticPool` (compartilha a conexão entre o fixture e a camada HTTP). Cada teste recebe um banco zerado via fixture `db` (escopo de função). O fixture `logged_in_client` fornece um cliente HTTP já autenticado como admin.

**11 arquivos de teste (~149+ casos):**
- `test_auth.py` — Login/logout
- `test_candidatos.py` — CRUD de candidatos
- `test_funcionarios.py` — CRUD + importação Excel
- `test_eleicao.py` — Abertura/encerramento de eleições
- `test_votacao.py` — Fluxo completo de votação pública
- `test_apuracao.py` — Apuração e regras de desempate
- `test_dimensionamento.py` — Dimensionamento NR-5 (todas as faixas)
- `test_relatorios.py` — Todos os 8 relatórios
- `test_historico.py` — Histórico de eleições
- `test_upload_funcionarios.py` — Importação via Excel
- `test_concorrencia.py` — Prevenção de voto duplicado

### Deploy

- **Produção:** Railway.app via `railway.toml` (Nixpacks, Gunicorn 5 workers)
- **Servidor:** `Procfile` — `gunicorn app:app`
- **Banco:** PostgreSQL em produção via variável de ambiente `DATABASE_URL`
