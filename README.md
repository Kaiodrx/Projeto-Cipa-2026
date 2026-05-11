# Sistema de Eleição CIPA 2026

Aplicação web desenvolvida em Flask para gerenciar o processo eleitoral da CIPA (Comissão Interna de Prevenção de Acidentes) da Neoenergia Brasília. Suporta múltiplas unidades com dimensionamento automático, apuração, desempate e relatórios obrigatórios.

---

## Índice

1. [O que o sistema faz](#o-que-o-sistema-faz)
2. [Dimensionamento da CIPA](#dimensionamento-da-cipa)
3. [Regras de apuração e desempate](#regras-de-apuração-e-desempate)
4. [Relatórios disponíveis](#relatórios-disponíveis)
5. [Requisitos](#requisitos)
6. [Instalação e execução local](#instalação-e-execução-local)
7. [Variáveis de ambiente](#variáveis-de-ambiente)
8. [Banco de dados](#banco-de-dados)
9. [Estrutura de pastas](#estrutura-de-pastas)
10. [Módulos principais](#módulos-principais)
11. [Testes automatizados](#testes-automatizados)
12. [Deploy (Railway)](#deploy-railway)

---

## O que o sistema faz

O sistema possui duas áreas:

**Área pública** — acessível por qualquer funcionário ativo:
- Página inicial com informações da eleição
- Login por matrícula e unidade para votar
- Tela de votação com lista de candidatos e fotos
- Confirmação de voto registrado

**Painel administrativo** (`/admin`) — restrito ao administrador:
- Gerenciar candidatos (cadastrar, remover, upload de foto, vincular a funcionário)
- Gerenciar funcionários com campos completos: matrícula, nome, unidade, setor, cargo, data de admissão, data de nascimento, status ativo/inativo
- **Administração da Eleição por unidade**: visualizar dimensionamento automático, eleitores, candidatos, votos, abrir/fechar eleição, acessar apuração e relatórios
- **Apuração detalhada por unidade**: ranking completo com titulares, suplentes e critério de desempate visível
- Acompanhar participação em tempo real
- Visualizar resultado geral e finalizar eleição (salvar no histórico)
- Emitir 8 tipos de relatórios por unidade (ver seção abaixo)
- Consultar histórico de eleições anteriores

**Unidades suportadas:** UTD Sobradinho, UTD Planaltina, UTD SIA, Sede Park Shopping, UTD Taguatinga, UTD Lago Sul, UTD São Sebastião, UTD Gama.

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

Acessíveis em `/admin/eleicao/<unidade>/relatorios`. Todos são páginas HTML com suporte a impressão (`@media print`).

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
| `Funcionario` | Eleitores: matrícula, nome, unidade, votou, ativo, data_admissao, data_nascimento, setor, cargo |
| `Candidato` | Candidatos por unidade: nome, cargo, foto, funcionario_id (FK opcional para desempate) |
| `Voto` | Registro de voto: candidato_id, funcionario_id (opcional), data_hora |
| `Eleicao` | Status da eleição por unidade: status, data_abertura, data_encerramento |
| `HistoricoEleicao` | Snapshot JSON de resultados finalizados com dimensionamento incluído |

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
│   │   │   ├── funcionarios.py # CRUD + novos campos + edição + importação Excel
│   │   │   ├── eleicao.py      # Adm. Eleição: abrir/fechar + dimensionamento
│   │   │   ├── apuracao.py     # Apuração detalhada por unidade
│   │   │   ├── relatorios.py   # 8 relatórios por unidade
│   │   │   ├── participacao.py # Participação em tempo real
│   │   │   ├── resultado.py    # Resultado geral + finalizar eleição
│   │   │   └── historico.py    # Histórico de eleições passadas
│   │   └── public/
│   │       └── votacao.py      # Home, login, votar, confirmação
│   └── services/
│       ├── foto.py             # Salvar, deletar, migrar fotos
│       ├── dimensionamento.py  # calcular_dimensionamento(n) — regra NR-5 GR3
│       └── apuracao.py         # apurar_eleicao(unidade) — ranking + desempate
│
├── templates/
│   ├── admin/
│   │   ├── eleicao.html            # Administração da Eleição (novo)
│   │   ├── apuracao.html           # Apuração por unidade (novo)
│   │   ├── relatorios_index.html   # Índice de relatórios por unidade (novo)
│   │   ├── funcionarios.html       # Com novos campos e modal de edição
│   │   ├── relatorios/             # 8 relatórios HTML print-friendly (novo)
│   │   │   ├── zeresima.html
│   │   │   ├── boletim.html
│   │   │   ├── cartaz.html
│   │   │   ├── eleitos.html
│   │   │   ├── classificacao.html
│   │   │   ├── votantes.html
│   │   │   ├── nao_votantes.html
│   │   │   └── eleitores.html
│   │   └── ... (demais templates existentes)
│   └── votacao/ ...
│
└── tests/
    ├── conftest.py
    ├── test_dimensionamento.py  # 34 testes das faixas NR-5 + acima de 10.000
    ├── test_apuracao.py         # 15 testes: ranking, desempate, situação, rotas
    ├── test_relatorios.py       # 15 testes: todos os 8 relatórios + proteção
    ├── test_eleicao.py          # Atualizado: novas rotas GET + data_abertura
    ├── test_funcionarios.py     # Atualizado: novos campos + edição + filtros
    └── ... (demais testes existentes)
```

---

## Módulos principais

### `app/services/dimensionamento.py`

Função `calcular_dimensionamento(num_funcionarios: int) -> dict` que retorna `{'titulares': int, 'suplentes': int}`. Encapsula a Tabela I da NR-5 para Grau de Risco 3. Independente de banco de dados — pode ser chamada de qualquer contexto.

### `app/services/apuracao.py`

Função `apurar_eleicao(unidade: str) -> dict` que calcula o resultado completo da eleição para uma unidade:
- Ordena candidatos por votos (desc) → data_admissao (asc) → nome (asc)
- Calcula `situacao` de cada candidato: Titular / Suplente / Não eleito
- Marca candidatos com `desempate_aplicado=True` quando há empate em votos
- Calcula totais de participação e percentuais

### `app/routes/admin/eleicao.py`

Rotas de administração da eleição. As ações individuais usam `GET /admin/eleicao/<unidade>/abrir|fechar` (path param com nome da unidade, espaços são URL-encoded automaticamente pelo Flask).

### `app/routes/admin/relatorios.py`

8 rotas de relatório, todas sob `/admin/eleicao/<unidade>/relatorio/<tipo>`. Usam `apurar_eleicao()` para dados ao vivo ou calculados.

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

### Organização (149 testes no total)

| Arquivo | Cobertura |
|---|---|
| `test_dimensionamento.py` | 34 testes: todas as faixas da tabela NR-5, acima de 10.000, entradas inválidas |
| `test_apuracao.py` | 15 testes: ordenação, desempate por admissão, desempate por nome, situação titular/suplente, rotas |
| `test_relatorios.py` | 15 testes: todos os 8 relatórios, zérésima, unidade inválida, proteção de rota |
| `test_eleicao.py` | Atualizado: novas rotas GET, data_abertura/encerramento, página de administração |
| `test_funcionarios.py` | Atualizado: novos campos (setor, cargo, datas), edição, filtro por ativo |
| `test_auth.py` | Login com sucesso/falha, proteção de rotas, logout |
| `test_votacao.py` | Voto válido, duplicado, eleição fechada, matrícula inválida, resultado |
| `test_candidatos.py` | CRUD de candidatos, listagem, remoção, proteção |
| `test_historico.py` | Listagem, detalhe, exclusão, rotas inexistentes, proteção |
| `test_upload_funcionarios.py` | Importação Excel com novos campos, modelo atualizado |
| `test_concorrencia.py` | Configuração de workers, múltiplos votantes, proteção contra voto duplo |

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
