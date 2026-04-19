"""
Fixtures compartilhadas entre todos os módulos de teste.

Estratégia de isolamento:
- `app` (session): criado uma vez; evita overhead de instanciar Flask repetidamente.
- `db` (function): recria tabelas e dados base a cada teste, garantindo isolamento total.
- `client` / `logged_in_client`: clientes HTTP que dependem do `db` e herdam seu contexto.
- Fixtures de domínio (candidato, funcionario, eleicao_aberta): criam objetos prontos para os testes.
"""
import os
import tempfile

import pytest
from sqlalchemy.pool import StaticPool
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db as _db
from app.models import Admin, Candidato, Eleicao, Funcionario, Voto
from app.constants import UNIDADES
from config import Config


# ── Config exclusiva para testes ──────────────────────────────────────────────

class TestingConfig(Config):
    TESTING = True
    # Banco em memória compartilhado via StaticPool: mesma conexão para fixture e requests.
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {'check_same_thread': False},
        'poolclass': StaticPool,
    }
    SECRET_KEY = 'test-secret-key'
    UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'cipa_test_uploads')
    WTF_CSRF_ENABLED = False


# Unidade usada como padrão em testes
UNIDADE = UNIDADES[0]  # 'UTD SOBRADINHO'


# ── Fixtures de infraestrutura ─────────────────────────────────────────────────

@pytest.fixture(scope='session')
def app():
    """Instância Flask criada uma única vez por sessão de testes."""
    os.makedirs(TestingConfig.UPLOAD_FOLDER, exist_ok=True)
    application = create_app(TestingConfig)
    yield application


@pytest.fixture()
def db(app):
    """
    Banco limpo por teste: cria tabelas, semeia dados base e descarta tudo ao final.
    Mantém o app context ativo para que consultas diretas ao ORM funcionem no teste.
    """
    ctx = app.app_context()
    ctx.push()

    _db.create_all()
    _semear_dados_base()

    yield _db

    _db.session.remove()
    _db.drop_all()
    ctx.pop()


def _semear_dados_base():
    """Dados mínimos presentes em todos os testes."""
    _db.session.add(Admin(
        username='admin',
        password=generate_password_hash('cipa2026'),
    ))
    for unidade in UNIDADES:
        _db.session.add(Eleicao(unidade=unidade, status='fechada'))
    _db.session.commit()


@pytest.fixture()
def client(app, db):
    """Cliente HTTP sem sessão admin ativa."""
    return app.test_client()


@pytest.fixture()
def logged_in_client(app, db):
    """Cliente HTTP já autenticado como admin."""
    c = app.test_client()
    resp = c.post('/admin/login', data={'username': 'admin', 'password': 'cipa2026'})
    assert resp.status_code == 302, 'Login deve redirecionar com credenciais corretas'
    return c


# ── Fixtures de domínio ────────────────────────────────────────────────────────

@pytest.fixture()
def candidato(db):
    """Candidato cadastrado na UNIDADE padrão."""
    c = Candidato(nome='João Silva', cargo='', unidade=UNIDADE)
    _db.session.add(c)
    _db.session.commit()
    return c


@pytest.fixture()
def funcionario(db):
    """Funcionário habilitado a votar na UNIDADE padrão (ainda não votou)."""
    f = Funcionario(
        matricula='MAT001',
        nome='Maria Santos',
        unidade=UNIDADE,
        votou=False,
    )
    _db.session.add(f)
    _db.session.commit()
    return f


@pytest.fixture()
def eleicao_aberta(db):
    """Abre a eleição da UNIDADE padrão."""
    eleicao = Eleicao.query.filter_by(unidade=UNIDADE).first()
    eleicao.status = 'aberta'
    _db.session.commit()
    return eleicao
