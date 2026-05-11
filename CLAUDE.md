# CLAUDE.md

Este arquivo fornece orientações ao Claude Code (claude.ai/code) ao trabalhar com o código deste repositório.

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

SQLAlchemy com SQLite (desenvolvimento) e PostgreSQL (produção via variável `DATABASE_URL`). `_init_db()` em `app/__init__.py` roda na inicialização: cria as tabelas, cria o admin padrão (`admin`/`cipa2026`) e uma linha de `Eleicao` por unidade. É idempotente — os ALTER TABLE são envolvidos em try/except.

Modelos: `Admin`, `Candidato`, `Funcionario`, `Voto`, `Eleicao`, `HistoricoEleicao`.

Os resultados da eleição são arquivados como snapshots JSON em `HistoricoEleicao.dados` (não em tabelas normalizadas), preservando o estado exato no momento da finalização.

### Unidades

7 unidades fixas definidas em `app/constants.py` (`UNIDADES`). Cada unidade tem sua própria linha em `Eleicao` com `status = 'aberta' | 'fechada'`. As eleições podem ser abertas/fechadas por unidade ou todas de uma vez.

### Upload de fotos

Fotos dos candidatos salvas em `static/uploads/` com nomes UUID. `app/services/foto.py` gerencia salvar/deletar. **Atenção:** no Railway (filesystem efêmero), as fotos são perdidas a cada redeploy — seria necessário integrar armazenamento em nuvem (S3/R2) para resolver isso.

### Testes

`tests/conftest.py` usa SQLite em memória com `StaticPool` (compartilha a conexão entre o fixture e a camada HTTP). Cada teste recebe um banco zerado via fixture `db` (escopo de função). O fixture `logged_in_client` fornece um cliente HTTP já autenticado como admin.
