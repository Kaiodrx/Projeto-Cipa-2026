"""
Testes das rotas de relatórios e zérésima.
Cobre: acesso autenticado/não-autenticado, unidade inválida, conteúdo básico.
"""
import pytest
from app.models import Candidato, Funcionario
from app.extensions import db as _db
from app.constants import UNIDADES

UNIDADE = UNIDADES[0]


def _setup_basico(db):
    """Cria um candidato e um funcionário na unidade padrão."""
    _db.session.add(Candidato(nome='Candidato Teste', cargo='', unidade=UNIDADE))
    _db.session.add(Funcionario(
        matricula='REL001', nome='Eleitor Teste', unidade=UNIDADE, ativo=True
    ))
    _db.session.commit()


# ── Zérésima ──────────────────────────────────────────────────────────────────

def test_zeresima_retorna_200(logged_in_client, db):
    resp = logged_in_client.get(f'/admin/eleicao/{UNIDADE}/relatorio/zeresima')
    assert resp.status_code == 200


def test_zeresima_exibe_candidatos(logged_in_client, db):
    _setup_basico(db)
    resp = logged_in_client.get(f'/admin/eleicao/{UNIDADE}/relatorio/zeresima')
    assert 'Candidato Teste' in resp.data.decode()


def test_zeresima_unidade_invalida_retorna_404(logged_in_client, db):
    resp = logged_in_client.get('/admin/eleicao/INVALIDA/relatorio/zeresima')
    assert resp.status_code == 404


def test_zeresima_sem_autenticacao_redireciona(client, db):
    resp = client.get(f'/admin/eleicao/{UNIDADE}/relatorio/zeresima', follow_redirects=True)
    assert 'Acesso Administrativo' in resp.data.decode()


# ── Índice de relatórios ───────────────────────────────────────────────────────

def test_relatorios_index_retorna_200(logged_in_client, db):
    resp = logged_in_client.get(f'/admin/eleicao/{UNIDADE}/relatorios')
    assert resp.status_code == 200


def test_relatorios_index_exibe_unidade(logged_in_client, db):
    resp = logged_in_client.get(f'/admin/eleicao/{UNIDADE}/relatorios')
    assert UNIDADE.encode() in resp.data


# ── Boletim da urna ───────────────────────────────────────────────────────────

def test_boletim_retorna_200(logged_in_client, db):
    resp = logged_in_client.get(f'/admin/eleicao/{UNIDADE}/relatorio/boletim')
    assert resp.status_code == 200


# ── Classificação ─────────────────────────────────────────────────────────────

def test_classificacao_retorna_200(logged_in_client, db):
    resp = logged_in_client.get(f'/admin/eleicao/{UNIDADE}/relatorio/classificacao')
    assert resp.status_code == 200


# ── Eleitos ───────────────────────────────────────────────────────────────────

def test_lista_eleitos_retorna_200(logged_in_client, db):
    resp = logged_in_client.get(f'/admin/eleicao/{UNIDADE}/relatorio/eleitos')
    assert resp.status_code == 200


# ── Listas de eleitores ───────────────────────────────────────────────────────

def test_lista_votantes_retorna_200(logged_in_client, db):
    resp = logged_in_client.get(f'/admin/eleicao/{UNIDADE}/relatorio/votantes')
    assert resp.status_code == 200


def test_lista_nao_votantes_retorna_200(logged_in_client, db):
    resp = logged_in_client.get(f'/admin/eleicao/{UNIDADE}/relatorio/nao-votantes')
    assert resp.status_code == 200


def test_lista_eleitores_retorna_200(logged_in_client, db):
    resp = logged_in_client.get(f'/admin/eleicao/{UNIDADE}/relatorio/eleitores')
    assert resp.status_code == 200


def test_lista_eleitores_exibe_funcionario(logged_in_client, db):
    _setup_basico(db)
    resp = logged_in_client.get(f'/admin/eleicao/{UNIDADE}/relatorio/eleitores')
    assert 'Eleitor Teste' in resp.data.decode()


# ── Cartaz ────────────────────────────────────────────────────────────────────

def test_cartaz_retorna_200(logged_in_client, db):
    resp = logged_in_client.get(f'/admin/eleicao/{UNIDADE}/relatorio/cartaz')
    assert resp.status_code == 200
