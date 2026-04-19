"""
Testes de gerenciamento de funcionários.
Cobre: cadastro, matrícula duplicada, remoção e proteção de rotas.
"""
import pytest
from app.extensions import db as _db
from app.models import Funcionario
from app.constants import UNIDADES

UNIDADE = UNIDADES[0]


# ── Cadastro ───────────────────────────────────────────────────────────────────

def test_adicionar_funcionario_com_sucesso(logged_in_client, db):
    resp = logged_in_client.post('/admin/funcionarios/adicionar', data={
        'matricula': 'MAT999',
        'nome': 'Carlos Teste',
        'unidade': UNIDADE,
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert Funcionario.query.filter_by(matricula='MAT999').first() is not None


def test_adicionar_funcionario_exibe_flash_sucesso(logged_in_client, db):
    resp = logged_in_client.post('/admin/funcionarios/adicionar', data={
        'matricula': 'MAT888',
        'nome': 'Ana Teste',
        'unidade': UNIDADE,
    }, follow_redirects=True)

    assert 'adicionado' in resp.data.decode().lower()


def test_matricula_duplicada_exibe_mensagem_de_erro(logged_in_client, db, funcionario):
    resp = logged_in_client.post('/admin/funcionarios/adicionar', data={
        'matricula': funcionario.matricula,  # MAT001 — já existe
        'nome': 'Outro Nome',
        'unidade': UNIDADE,
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert 'já cadastrada' in resp.data.decode()


def test_matricula_duplicada_nao_cria_registro(logged_in_client, db, funcionario):
    logged_in_client.post('/admin/funcionarios/adicionar', data={
        'matricula': funcionario.matricula,
        'nome': 'Outro Nome',
        'unidade': UNIDADE,
    })

    total = Funcionario.query.filter_by(matricula=funcionario.matricula).count()
    assert total == 1


# ── Remoção ────────────────────────────────────────────────────────────────────

def test_remover_funcionario_com_sucesso(logged_in_client, db, funcionario):
    fid = funcionario.id
    resp = logged_in_client.get(
        f'/admin/funcionarios/remover/{fid}',
        follow_redirects=True,
    )

    assert resp.status_code == 200
    _db.session.expire_all()
    assert Funcionario.query.get(fid) is None


def test_remover_funcionario_exibe_flash(logged_in_client, db, funcionario):
    resp = logged_in_client.get(
        f'/admin/funcionarios/remover/{funcionario.id}',
        follow_redirects=True,
    )
    assert 'removido' in resp.data.decode().lower()


def test_remover_funcionario_inexistente_retorna_404(logged_in_client, db):
    resp = logged_in_client.get('/admin/funcionarios/remover/99999')
    assert resp.status_code == 404


# ── Proteção de rota ───────────────────────────────────────────────────────────

def test_adicionar_funcionario_sem_autenticacao_redireciona(client):
    resp = client.post('/admin/funcionarios/adicionar', data={
        'matricula': 'MAT777',
        'nome': 'Invasor',
        'unidade': UNIDADE,
    }, follow_redirects=True)

    assert 'Acesso Administrativo' in resp.data.decode()
    assert Funcionario.query.filter_by(matricula='MAT777').first() is None
