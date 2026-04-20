"""
Testes de gerenciamento de candidatos.
Cobre: cadastro, remoção e proteção de rotas.
"""
import pytest
from app.extensions import db as _db
from app.models import Candidato
from app.constants import UNIDADES

UNIDADE = UNIDADES[0]


# ── Cadastro ───────────────────────────────────────────────────────────────────

def test_adicionar_candidato_com_sucesso(logged_in_client, db):
    resp = logged_in_client.post('/admin/candidatos/adicionar', data={
        'nome': 'Pedro Teste',
        'unidade': UNIDADE,
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert Candidato.query.filter_by(nome='Pedro Teste').first() is not None


def test_adicionar_candidato_exibe_flash_sucesso(logged_in_client, db):
    resp = logged_in_client.post('/admin/candidatos/adicionar', data={
        'nome': 'Ana Teste',
        'unidade': UNIDADE,
    }, follow_redirects=True)

    assert 'adicionado' in resp.data.decode().lower()


def test_adicionar_candidato_sem_nome_nao_cria_registro(logged_in_client, db):
    logged_in_client.post('/admin/candidatos/adicionar', data={
        'nome': '',
        'unidade': UNIDADE,
    })

    assert Candidato.query.count() == 0


def test_adicionar_candidato_sem_unidade_nao_cria_registro(logged_in_client, db):
    logged_in_client.post('/admin/candidatos/adicionar', data={
        'nome': 'Sem Unidade',
        'unidade': '',
    })

    assert Candidato.query.count() == 0


# ── Listagem ───────────────────────────────────────────────────────────────────

def test_listar_candidatos_retorna_200(logged_in_client, db):
    resp = logged_in_client.get('/admin/candidatos')
    assert resp.status_code == 200


def test_listar_candidatos_exibe_candidato_cadastrado(logged_in_client, db, candidato):
    resp = logged_in_client.get('/admin/candidatos')
    assert candidato.nome in resp.data.decode()


# ── Remoção ────────────────────────────────────────────────────────────────────

def test_remover_candidato_com_sucesso(logged_in_client, db, candidato):
    cid = candidato.id
    resp = logged_in_client.get(
        f'/admin/candidatos/remover/{cid}',
        follow_redirects=True,
    )

    assert resp.status_code == 200
    _db.session.expire_all()
    assert Candidato.query.get(cid) is None


def test_remover_candidato_exibe_flash(logged_in_client, db, candidato):
    resp = logged_in_client.get(
        f'/admin/candidatos/remover/{candidato.id}',
        follow_redirects=True,
    )
    assert 'removido' in resp.data.decode().lower()


def test_remover_candidato_inexistente_retorna_404(logged_in_client, db):
    resp = logged_in_client.get('/admin/candidatos/remover/99999')
    assert resp.status_code == 404


# ── Proteção de rota ───────────────────────────────────────────────────────────

def test_adicionar_candidato_sem_autenticacao_redireciona(client, db):
    resp = client.post('/admin/candidatos/adicionar', data={
        'nome': 'Invasor',
        'unidade': UNIDADE,
    }, follow_redirects=True)

    assert 'Acesso Administrativo' in resp.data.decode()
    assert Candidato.query.filter_by(nome='Invasor').first() is None


def test_listar_candidatos_sem_autenticacao_redireciona(client, db):
    resp = client.get('/admin/candidatos', follow_redirects=True)
    assert 'Acesso Administrativo' in resp.data.decode()
