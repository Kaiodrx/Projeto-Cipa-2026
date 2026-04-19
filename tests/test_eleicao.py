"""
Testes de gerenciamento de eleições.
Cobre: abrir/fechar individual, abrir/fechar todas, proteção de rota.
"""
import pytest
from app.extensions import db as _db
from app.models import Eleicao
from app.constants import UNIDADES

UNIDADE = UNIDADES[0]


# ── Abrir / fechar individual ──────────────────────────────────────────────────

def test_abrir_eleicao_individual(logged_in_client, db):
    resp = logged_in_client.get(
        f'/admin/eleicao/{UNIDADE}/abrir',
        follow_redirects=True,
    )
    assert resp.status_code == 200

    _db.session.expire_all()
    eleicao = Eleicao.query.filter_by(unidade=UNIDADE).first()
    assert eleicao.status == 'aberta'


def test_fechar_eleicao_individual(logged_in_client, db, eleicao_aberta):
    resp = logged_in_client.get(
        f'/admin/eleicao/{UNIDADE}/fechar',
        follow_redirects=True,
    )
    assert resp.status_code == 200

    _db.session.expire_all()
    eleicao = Eleicao.query.filter_by(unidade=UNIDADE).first()
    assert eleicao.status == 'fechada'


def test_abrir_eleicao_exibe_flash_sucesso(logged_in_client, db):
    resp = logged_in_client.get(
        f'/admin/eleicao/{UNIDADE}/abrir',
        follow_redirects=True,
    )
    assert 'aberta' in resp.data.decode().lower()


def test_fechar_eleicao_exibe_flash(logged_in_client, db, eleicao_aberta):
    resp = logged_in_client.get(
        f'/admin/eleicao/{UNIDADE}/fechar',
        follow_redirects=True,
    )
    assert 'encerrada' in resp.data.decode().lower()


def test_abrir_unidade_inexistente_retorna_404(logged_in_client, db):
    resp = logged_in_client.get('/admin/eleicao/UNIDADE_INVALIDA/abrir')
    assert resp.status_code == 404


# ── Abrir / fechar todas ───────────────────────────────────────────────────────

def test_abrir_todas_abre_todas_as_unidades(logged_in_client, db):
    logged_in_client.get('/admin/eleicao/abrir-todas', follow_redirects=True)

    _db.session.expire_all()
    fechadas = Eleicao.query.filter_by(status='fechada').count()
    assert fechadas == 0


def test_fechar_todas_fecha_todas_as_unidades(logged_in_client, db):
    # Garante que há ao menos uma aberta antes de fechar todas
    logged_in_client.get('/admin/eleicao/abrir-todas')

    logged_in_client.get('/admin/eleicao/fechar-todas', follow_redirects=True)

    _db.session.expire_all()
    abertas = Eleicao.query.filter_by(status='aberta').count()
    assert abertas == 0


def test_abrir_todas_exibe_flash_sucesso(logged_in_client, db):
    resp = logged_in_client.get('/admin/eleicao/abrir-todas', follow_redirects=True)
    assert 'abertas' in resp.data.decode().lower()


# ── Proteção de rota ───────────────────────────────────────────────────────────

def test_gerenciar_eleicao_sem_autenticacao_redireciona(client):
    resp = client.get('/admin/eleicao', follow_redirects=True)
    assert 'Acesso Administrativo' in resp.data.decode()


def test_abrir_eleicao_sem_autenticacao_redireciona(client):
    resp = client.get(f'/admin/eleicao/{UNIDADE}/abrir', follow_redirects=True)
    assert 'Acesso Administrativo' in resp.data.decode()
