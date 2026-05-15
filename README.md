# Sistema de Eleição CIPA 2026

Aplicação web desenvolvida em Flask para gerenciar o processo eleitoral da CIPA (Comissão Interna de Prevenção de Acidentes) da Neoenergia Brasília. Suporta múltiplas unidades com dimensionamento automático, apuração, desempate e relatórios obrigatórios.

---

## Índice

1. [O que o sistema faz](#o-que-o-sistema-faz)
2. [Autenticação do eleitor](#autenticação-do-eleitor)
3. [Participação — Dashboard gerencial](#participação--dashboard-gerencial)
4. [Dimensionamento da CIPA](#dimensionamento-da-cipa)
5. [Regras de apuração e desempate](#regras-de-apuração-e-desempate)
6. [Relatórios disponíveis](#relatórios-disponíveis)
7. [Requisitos](#requisitos)
8. [Instalação e execução local](#instalação-e-execução-local)
9. [Variáveis de ambiente](#variáveis-de-ambiente)
10. [Banco de dados](#banco-de-dados)
11. [Estrutura de pastas](#estrutura-de-pastas)
12. [Módulos principais](#módulos-principais)
13. [Testes automatizados](#testes-automatizados)
14. [Deploy (Railway)](#deploy-railway)

---

## O que o sistema faz

O sistema possui duas áreas:

**Área pública** — acessível por qualquer funcionário ativo:
- Página inicial com informações da eleição
- Login por matrícula, unidade **e data de nascimento** para acessar a votação
- Tela de votação com lista de candidatos e fotos
- Confirmação de voto registrado

**Painel administrativo** (`/admin`) — restrito ao administrador:
- Gerenciar candidatos (cadastrar, remover, upload de foto, vincular a funcionário)
- Gerenciar funcionários com campos completos: matrícula, nome, unidade, setor, cargo, data de admissão, data de nascimento, status ativo/inativo
- **Administração da Eleição por unidade**: visualizar dimensionamento automático, eleitores, candidatos, votos, abrir/fechar eleição, acessar apuração e relatórios
- **Apuração detalhada por unidade**: ranking completo com titulares, suplentes e critério de desempate visível
- **Dashboard de participação por unidade** com indicador de validade (≥ 50%)
- Visualizar resultado geral e finalizar eleição (salvar no histórico)
- Emitir 10 tipos de relatórios (ver seção abaixo)
- Consultar histórico de eleições anteriores

**Unidades suportadas:** UTD Sobradinho, UTD Planaltina, UTD SIA, Sede Park Shopping, UTD Taguatinga, UTD Lago Sul, UTD São Sebastião, UTD Gama.

---

## Autenticação do eleitor

Para acessar a votação, o funcionário deve informar três dados:

1. **Matrícula** — identificador único do funcionário
2. **Unidade** — unidade à qual pertence
3. **Data de nascimento** — confirmação de identidade

O sistema só libera o acesso quando **todos os três dados conferem** com o cadastro e a eleição da unidade está aberta. Se qualquer dado estiver errado, é exibida uma mensagem genérica sem revelar qual campo falhou — isso impede que alguém tente descobrir se uma matrícula existe no sistema.

**Serviço:** `app/services/eleitor.py` — função `validar_eleitor(matricula, unidade, data_nascimento_str)`.

Retorna `(funcionario, None)` quando tudo está correto, ou `(None, mensagem_de_erro)` quando há problema. Cada condição de erro tem tratamento específico:

| Situação | Mensagem exibida |
|---|---|
| Matrícula não encontrada / unidade errada / data de nascimento errada | Dados não conferem. Verifique matrícula, unidade e data de nascimento. |
| Funcionário inativo | Você não está habilitado a votar nesta eleição. |
| Funcionário já votou | Você já votou nesta eleição. |
| Eleição fechada | A eleição desta unidade não está aberta no momento. |

---

## Participação — Dashboard gerencial

A página de participação (`/admin/participacao`) exibe um **dashboard consolidado por unidade** — sem listar nomes de funcionários na tela principal. O objetivo é dar uma visão executiva do andamento da eleição.

### O que o dashboard exibe por unidade

- Total de funcionários elegíveis (ativos)
- Total de votos computados
- Total de pendentes
- Percentual de participação
- Badge de status: **Válida** (verde) ou **Abaixo do mínimo** (vermelho)
- Barra de progresso com marcador visual no limiar de 50%

### Regra de validação da eleição

> A eleição de uma unidade é considerada **válida** quando a participação for **≥ 50%** dos funcionários elegíveis (ativos).

- Base de cálculo: `funcionarios.ativo = True`
- Fórmula: `(votos / total_ativos) × 100`
- O limiar de 50% é marcado visualmente em todas as barras de progresso

**Serviço:** `app/services/participacao.py` — funções `calcular_participacao_unidade(unidade)` e `calcular_participacao_geral()`.

---

## Dimensionamento da CIPA

O sistema calcula automaticamente a quantidade de **Titulares** e **Suplentes** da CIPA por unidade, com base no número de eleitores ativos e no **Grau de Risco 3** (NR-5, Tabela I).

Serviço: `app/services/dimensionamento.py` — função `calcular_dimensionamento(num_funcionarios)`.

### Tabela de dimensionamento (Grau de Risco 3)

| Funcionários | Titulares | Suplentes |
|---|---|---|
| 0 a 19 | 0 | 0 |
| 20 a 29 | 1 | 1 |
| 30 a 50 | 1 | 1 |
| 51 a 80 | 2 | 1 |
| 81 a 100 | 2 | 1 |
| 101 a 120 | 2 | 1 |
| 121 a 140 | 3 | 2 |
| 141 a 300 | 4 | 2 |
| 301 a 500 | 5 | 4 |
| 501 a 1.000 | 6 | 4 |
| 1.001 a 2.500 | 8 | 6 |
| 2.501 a 5.000 | 10 | 8 |
| 5.001 a 10.000 | 12 | 8 |
| Acima de 10.000 | +2 por grupo de 2.500 | +2 por grupo de 2.500 |

**Regra acima de 10.000:** Para cada grupo adicional de 2.500 funcionários acima de 10.000, acrescenta-se 2 titulares e 2 suplentes. Grupos parciais contam como completos (arredondamento para cima — `math.ceil`).

Exemplos:
- 10.001 a 12.500 → 1 grupo adicional → **14 titulares, 10 suplentes**
- 12.501 a 15.000 → 2 grupos → **16 titulares, 12 suplentes**

---

## Regras de apuração e desempate

Serviço: `app/services/apuracao.py` — função `apurar_eleicao(unidade)`.

### Ordenação dos candidatos

1. **Número de votos** (decrescente) — critério principal
2. **Data de admissão mais antiga** (crescente) — 1º critério de desempate: funcionário mais antigo tem prioridade
3. **Nome em ordem alfabética** (crescente) — 2º critério de desempate: determinístico e auditável

O critério de desempate é aplicado automaticamente e sinalizado na tela de apuração com o badge **"Desempate"** ao lado dos candidatos afetados.

### Vínculo candidato → funcionário

Para usar a data de admissão no desempate, o candidato precisa estar vinculado ao funcionário correspondente pelo campo `funcionario_id` na tela de candidatos. Candidatos sem vínculo são tratados como sem data de admissão e ficam no final do grupo empatado (resolvido pelo nome).

---

## Relatórios disponíveis

Todos os relatórios são páginas HTML otimizadas para impressão direta pelo navegador (`@media print`).

### Relatórios por unidade

Acessíveis em `/admin/eleicao/<unidade>/relatorios`.

| Relatório | URL | Descrição |
|---|---|---|
| Zérésima | `.../relatorio/zeresima` | Todos os candidatos com 0 votos antes da eleição |
| Boletim da Urna | `.../relatorio/boletim` | Totais, participação e ranking completo |
| Cartaz dos Eleitos | `.../relatorio/cartaz` | Layout visual para afixar com fotos dos eleitos |
| Lista dos Eleitos | `.../relatorio/eleitos` | Titulares e suplentes com votos e percentual |
| Classificação dos Candidatos | `.../relatorio/classificacao` | Ranking completo com situação final |
| Eleitores Votantes | `.../relatorio/votantes` | Quem votou com data/hora do voto |
| Eleitores Não Votantes | `.../relatorio/nao-votantes` | Eleitores ativos que ainda não votaram |
| Lista de Eleitores Ativos | `.../relatorio/eleitores` | Cadastro completo com todos os campos |

### Relatórios de participação

Acessíveis diretamente na página de participação (`/admin/participacao`) pelos botões de relatório.

| Relatório | URL | Descrição |
|---|---|---|
| Participação — Dashboard | `/admin/relatorio/participacao/dashboard` | Visão consolidada por unidade: elegíveis, votos, percentual e status de validade. Sem nomes. Ideal para acompanhamento gerencial e impressão. |
| Participação — Nominal | `/admin/relatorio/participacao/nominal` | Lista detalhada de funcionários por unidade com status de participação (Votou / Pendente). Aceita `?unidade=NOME` para filtrar por unidade. |

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
| openpyxl | 3.1.5 | Leitura e geração de arquivos Excel (.xlsx) |

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

### 4. Rodar a aplicação

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
| `DATABASE_URL` | `sqlite:///cipa.db` | URI do banco de dados. Em produção, usar PostgreSQL. |

---

## Banco de dados

### Tecnologia

Em desenvolvimento: **SQLite** (arquivo `instance/cipa.db`, criado automaticamente).
Em produção: recomenda-se **PostgreSQL** via variável `DATABASE_URL`.

### Modelos (tabelas)

| Modelo | Descrição |
|---|---|
| `Admin` | Usuário administrador com senha em hash |
| `Funcionario` | Eleitores: matrícula, nome, unidade, votou, ativo, data_admissao, **data_nascimento**, setor, cargo |
| `Candidato` | Candidatos por unidade: nome, cargo, foto, funcionario_id (FK opcional para desempate) |
| `Voto` | Registro de voto: candidato_id, funcionario_id (opcional), data_hora |
| `Eleicao` | Status da eleição por unidade: status, data_abertura, data_encerramento |
| `HistoricoEleicao` | Snapshot JSON de resultados finalizados com dimensionamento incluído |

O campo `data_nascimento` do modelo `Funcionario` é obrigatório para o acesso à votação. Funcionários sem esse campo cadastrado ficam impedidos de votar até que o campo seja preenchido.

### Migração incremental

O sistema usa `ALTER TABLE ... ADD COLUMN` com `try/except` para adicionar colunas novas sem destruir dados existentes em produção. Isso acontece automaticamente em cada reinício da aplicação (`_init_db()`).

### Fotos de candidatos

Fotos são salvas em `static/uploads/` com nome UUID. O banco armazena apenas o caminho relativo. Limite: **16 MB** por arquivo. Formatos: `jpg`, `jpeg`, `png`, `gif`.

> **Atenção (produção):** plataformas como Railway têm filesystem efêmero — uploads são perdidos a cada redeploy. Para persistência, integrar `app/services/foto.py` com AWS S3 ou equivalente.

---

## Estrutura de pastas

```
Projeto-Cipa-2026/
├── run.py
├── config.py
├── requirements.txt
├── app/
│   ├── __init__.py             # Application factory + _init_db()
│   ├── models.py               # Admin, Funcionario, Candidato, Voto, Eleicao, HistoricoEleicao
│   ├── constants.py            # UNIDADES, ALLOWED_EXTENSIONS
│   ├── utils.py                # @login_required
│   ├── routes/
│   │   ├── admin/
│   │   │   ├── auth.py         # Login/logout
│   │   │   ├── dashboard.py    # Painel principal
│   │   │   ├── candidatos.py   # CRUD candidatos + vincular funcionário
│   │   │   ├── funcionarios.py # CRUD + campos completos + importação Excel
│   │   │   ├── eleicao.py      # Adm. Eleição: abrir/fechar + dimensionamento
│   │   │   ├── apuracao.py     # Apuração detalhada por unidade
│   │   │   ├── relatorios.py   # 10 relatórios (8 por unidade + 2 de participação)
│   │   │   ├── participacao.py # Dashboard de participação por unidade
│   │   │   ├── resultado.py    # Resultado geral + finalizar eleição
│   │   │   └── historico.py    # Histórico de eleições passadas
│   │   └── public/
│   │       └── votacao.py      # Home, login, votar, confirmação
│   └── services/
│       ├── eleitor.py          # validar_eleitor() — autenticação com data de nascimento
│       ├── participacao.py     # calcular_participacao_geral/unidade() — regra dos 50%
│       ├── foto.py             # Salvar, deletar, migrar fotos
│       ├── dimensionamento.py  # calcular_dimensionamento(n) — regra NR-5 GR3
│       └── apuracao.py         # apurar_eleicao(unidade) — ranking + desempate
│
├── templates/
│   ├── admin/
│   │   ├── participacao.html           # Dashboard gerencial por unidade
│   │   ├── eleicao.html                # Administração da Eleição
│   │   ├── apuracao.html               # Apuração por unidade
│   │   ├── relatorios_index.html       # Índice de relatórios por unidade
│   │   ├── funcionarios.html           # Com campos completos e modal de edição
│   │   └── relatorios/                 # 10 templates print-friendly
│   │       ├── zeresima.html
│   │       ├── boletim.html
│   │       ├── cartaz.html
│   │       ├── eleitos.html
│   │       ├── classificacao.html
│   │       ├── votantes.html
│   │       ├── nao_votantes.html
│   │       ├── eleitores.html
│   │       ├── participacao_dashboard.html  # Novo: consolidado por unidade
│   │       └── participacao_nominal.html    # Novo: nominal com filtro por unidade
│   └── votacao/
│       ├── login.html       # Com campo de data de nascimento
│       ├── votar.html
│       └── confirmacao.html
│
└── tests/
    ├── conftest.py
    ├── test_auth.py
    ├── test_candidatos.py
    ├── test_funcionarios.py
    ├── test_eleicao.py
    ├── test_votacao.py          # Atualizado: validação por data de nascimento
    ├── test_apuracao.py
    ├── test_dimensionamento.py
    ├── test_relatorios.py
    ├── test_participacao.py     # Novo: cálculo de participação + relatórios
    ├── test_historico.py
    ├── test_upload_funcionarios.py
    └── test_concorrencia.py    # Atualizado: inclui data_nascimento nos POSTs
```

---

## Módulos principais

### `app/services/eleitor.py`

Função `validar_eleitor(matricula, unidade, data_nascimento_str) -> tuple`.

Centraliza toda a lógica de validação do eleitor antes do acesso à votação. Recebe os três dados do formulário e retorna `(funcionario, None)` em caso de sucesso ou `(None, mensagem_erro)` em caso de falha. A mesma mensagem genérica é usada para matrícula inválida, unidade incorreta e data de nascimento errada, evitando enumeração de usuários.

### `app/services/participacao.py`

Duas funções principais:

- `calcular_participacao_unidade(unidade: str) -> dict` — retorna `{total, votaram, pendentes, percentual, valida}` para uma unidade. Base de cálculo: funcionários com `ativo=True`.
- `calcular_participacao_geral() -> dict` — retorna o consolidado de todas as unidades mais a lista `por_unidade`.

Constante `PERCENTUAL_MINIMO = 50.0` define o limiar de validade.

### `app/services/dimensionamento.py`

Função `calcular_dimensionamento(num_funcionarios: int) -> dict` que retorna `{'titulares': int, 'suplentes': int}`. Encapsula a Tabela I da NR-5 para Grau de Risco 3. Independente de banco de dados — pode ser chamada de qualquer contexto.

### `app/services/apuracao.py`

Função `apurar_eleicao(unidade: str) -> dict` que calcula o resultado completo da eleição para uma unidade:
- Ordena candidatos por votos (desc) → data_admissao (asc) → nome (asc)
- Calcula `situacao` de cada candidato: Titular / Suplente / Não eleito
- Marca candidatos com `desempate_aplicado=True` quando há empate em votos
- Calcula totais de participação e percentuais

### `app/routes/admin/relatorios.py`

10 rotas de relatório:
- 8 rotas sob `/admin/eleicao/<unidade>/relatorio/<tipo>`
- `/admin/relatorio/participacao/dashboard` — relatório consolidado de participação
- `/admin/relatorio/participacao/nominal` — relatório nominal com filtro `?unidade=`

---

## Testes automatizados

### Rodar todos os testes

```bash
pytest
```

### Rodar com cobertura

```bash
pytest --cov=app --cov-report=term-missing
```

### Organização (179 testes no total)

| Arquivo | Cobertura |
|---|---|
| `test_dimensionamento.py` | 34 testes: todas as faixas da tabela NR-5, acima de 10.000, entradas inválidas |
| `test_apuracao.py` | 15 testes: ordenação, desempate por admissão, desempate por nome, situação titular/suplente, rotas |
| `test_relatorios.py` | 15 testes: todos os 8 relatórios por unidade, zérésima, unidade inválida, proteção de rota |
| `test_participacao.py` | 27 testes: cálculo por unidade, regra de 50%, funcionários inativos, rotas dashboard e nominal, filtro por unidade |
| `test_votacao.py` | 16 testes: validação por data de nascimento (correta, incorreta, ausente, formato inválido), voto válido, duplicado, eleição fechada |
| `test_eleicao.py` | Abertura/fechamento por unidade e todas, data_abertura/encerramento, proteção |
| `test_funcionarios.py` | CRUD com campos completos (setor, cargo, datas), edição, filtro por ativo, importação |
| `test_auth.py` | Login com sucesso/falha, proteção de rotas, logout |
| `test_candidatos.py` | CRUD de candidatos, listagem, remoção, proteção |
| `test_historico.py` | Listagem, detalhe, exclusão, rotas inexistentes, proteção |
| `test_upload_funcionarios.py` | Importação Excel, modelo de planilha, validações |
| `test_concorrencia.py` | Configuração de workers, múltiplos votantes com data_nascimento, proteção contra voto duplo |

> **Nota para novos testes:** o fixture `funcionario` em `conftest.py` tem `data_nascimento=date(1985, 7, 20)`. Qualquer teste que faça POST em `/votacao` deve incluir `'data_nascimento': '1985-07-20'` no corpo da requisição.

---

## Deploy (Railway)

O projeto está configurado para deploy automático no [Railway](https://railway.app).

- **`Procfile`**: `web: gunicorn run:app --bind 0.0.0.0:$PORT --workers 5`
- **`railway.toml`**: builder Nixpacks, 5 workers, healthcheck em `/`

### Variáveis obrigatórias

| Variável | Valor |
|---|---|
| `SECRET_KEY` | String aleatória longa |
| `DATABASE_URL` | URI do banco PostgreSQL |

### Limitações conhecidas

- **Uploads de fotos não persistem** entre deploys (filesystem efêmero do Railway). Solução: integrar com AWS S3 ou Cloudflare R2.
- **Sem migrations automáticas**: a migração incremental via `ALTER TABLE` cobre adições de coluna, mas não renomeações ou remoções.

---

Desenvolvido para a Neoenergia Brasília — Processo Eleitoral CIPA 2026.
