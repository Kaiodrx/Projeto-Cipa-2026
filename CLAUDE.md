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

- **`eleitor.py`** — Valida o eleitor antes do acesso à votação. Função `validar_eleitor(matricula, unidade, data_nascimento_str)` retorna `(funcionario, None)` em caso de sucesso ou `(None, mensagem_erro)` em caso de falha. Usa mensagem genérica para matrícula inválida / unidade incorreta / data de nascimento errada para evitar enumeração de usuários.
- **`participacao.py`** — Calcula participação por unidade e geral. `calcular_participacao_unidade(unidade)` e `calcular_participacao_geral()`. Base de cálculo = funcionários ativos (`ativo=True`). `PERCENTUAL_MINIMO = 50.0`. Retorna `{'total', 'votaram', 'pendentes', 'percentual', 'valida'}`.
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

### Autenticação do eleitor

O acesso à votação (`/votacao`) exige três campos: **matrícula**, **unidade** e **data de nascimento**. A validação é feita pelo serviço `app/services/eleitor.py → validar_eleitor()`. A ordem de verificação é:

1. Formato válido da data de nascimento (YYYY-MM-DD, enviado pelo `<input type="date">`)
2. Matrícula existe no banco
3. Unidade confere com o cadastro do funcionário
4. Data de nascimento confere com o cadastro
5. Funcionário está ativo
6. Funcionário ainda não votou
7. Eleição da unidade está aberta

Os passos 2, 3 e 4 usam a mesma mensagem genérica de erro para evitar que alguém descubra se uma matrícula existe apenas tentando logins.

### Participação — Dashboard gerencial

`/admin/participacao` exibe um dashboard consolidado por unidade (não lista nominal). Usa `app/services/participacao.py`. Regra de validação: eleição considerada válida por unidade quando participação ≥ 50% dos funcionários ativos. A interface mostra um marcador visual do limiar de 50% na barra de progresso.

### Relatórios (`app/routes/admin/relatorios.py`)

10 relatórios, todos otimizados para impressão direta pelo navegador (`@media print`):

| Relatório | Rota | Conteúdo |
|---|---|---|
| Zerésima | `/admin/eleicao/<unidade>/relatorio/zeresima` | Candidatos com zero votos (pré-eleição) |
| Boletim | `/admin/eleicao/<unidade>/relatorio/boletim` | Resumo da cédula com participação |
| Cartaz | `/admin/eleicao/<unidade>/relatorio/cartaz` | Pôster visual dos eleitos |
| Eleitos | `/admin/eleicao/<unidade>/relatorio/eleitos` | Lista de titulares e suplentes eleitos |
| Classificação | `/admin/eleicao/<unidade>/relatorio/classificacao` | Ranking completo com status final |
| Votantes | `/admin/eleicao/<unidade>/relatorio/votantes` | Quem votou com horário |
| Não-votantes | `/admin/eleicao/<unidade>/relatorio/nao-votantes` | Quem não votou |
| Eleitores | `/admin/eleicao/<unidade>/relatorio/eleitores` | Cadastro completo do eleitorado |
| Participação Dashboard | `/admin/relatorio/participacao/dashboard` | Visão consolidada por unidade (sem nomes), pronto para impressão gerencial |
| Participação Nominal | `/admin/relatorio/participacao/nominal` | Lista de funcionários por unidade com status de participação. Aceita `?unidade=` para filtrar por unidade |

### Upload de fotos

Fotos dos candidatos salvas em `static/uploads/` com nomes UUID. `app/services/foto.py` gerencia salvar/deletar. **Atenção:** no Railway (filesystem efêmero), as fotos são perdidas a cada redeploy — seria necessário integrar armazenamento em nuvem (S3/R2) para resolver isso.

### Importação de funcionários

Rota em `app/routes/admin/funcionarios.py` aceita planilha Excel (`.xlsx`) via `openpyxl`. Cria ou atualiza funcionários pelos campos: matrícula, nome, unidade, setor, cargo, data de admissão, data de nascimento.

### Testes

`tests/conftest.py` usa SQLite em memória com `StaticPool` (compartilha a conexão entre o fixture e a camada HTTP). Cada teste recebe um banco zerado via fixture `db` (escopo de função). O fixture `logged_in_client` fornece um cliente HTTP já autenticado como admin.

**12 arquivos de teste (179 casos):**
- `test_auth.py` — Login/logout
- `test_candidatos.py` — CRUD de candidatos
- `test_funcionarios.py` — CRUD + importação Excel
- `test_eleicao.py` — Abertura/encerramento de eleições
- `test_votacao.py` — Fluxo completo de votação pública, incluindo validação por data de nascimento
- `test_apuracao.py` — Apuração e regras de desempate
- `test_dimensionamento.py` — Dimensionamento NR-5 (todas as faixas)
- `test_relatorios.py` — Os 8 relatórios por unidade
- `test_participacao.py` — Cálculo de participação + relatórios dashboard e nominal
- `test_historico.py` — Histórico de eleições
- `test_upload_funcionarios.py` — Importação via Excel
- `test_concorrencia.py` — Prevenção de voto duplicado

**Campos obrigatórios do fixture `funcionario` (conftest.py):** `data_nascimento=date(1985, 7, 20)`. Testes que fazem login de votação devem incluir `'data_nascimento': '1985-07-20'` no POST.

### Deploy

- **Produção:** Railway.app via `railway.toml` (Nixpacks, Gunicorn 5 workers)
- **Servidor:** `Procfile` — `gunicorn app:app`
- **Banco:** PostgreSQL em produção via variável de ambiente `DATABASE_URL`
