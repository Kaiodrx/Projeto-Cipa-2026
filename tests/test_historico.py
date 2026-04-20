"""
Testes do histórico de eleições.
Cobre: listagem, visualização de detalhe, exclusão e proteção de rotas.
"""
import json
import pytest
from app.extensions import db as _db
from app.models import HistoricoEleicao


SNAPSHOT_BASE = {
    'titulo': 'Eleição Teste',
    'data': '01/01/2026 às 10:00',
    'total_geral': 10,
    'unidades': [
        {
            'unidade': 'UTD SOBRADINHO',
            'total_votos': 10,
            'votaram': 8,
            'total_funcionarios': 10,
            'candidatos': [
                {'nome': 'João Silva', 'foto': None, 'votos': 7, 'pct': 70.0},
                {'nome': 'Maria Lima', 'foto': None, 'votos': 3, 'pct': 30.0},
            ],
        }
    ],
}


def _criar_historico(titulo='Eleição Teste'):
    snap = dict(SNAPSHOT_BASE, titulo=titulo)
    h = HistoricoEleicao(titulo=titulo, dados=json.dumps(snap))
    _db.session.add(h)
    _db.session.commit()
    return h


# ── Listagem ───────────────────────────────────────────────────────────────────

def test_historico_vazio_retorna_200(logged_in_client, db):
    resp = logged_in_client.get('/admin/historico')
    assert resp.status_code == 200


def test_historico_exibe_registro_cadastrado(logged_in_client, db):
    _criar_historico('Eleição CIPA 2026')
    resp = logged_in_client.get('/admin/historico')
    assert 'Eleição CIPA 2026' in resp.data.decode()


def test_historico_exibe_vencedor_da_unidade(logged_in_client, db):
    _criar_historico()
    resp = logged_in_client.get('/admin/historico')
    assert 'João Silva' in resp.data.decode()


# ── Detalhe ────────────────────────────────────────────────────────────────────

def test_ver_historico_retorna_200(logged_in_client, db):
    h = _criar_historico()
    resp = logged_in_client.get(f'/admin/historico/{h.id}')
    assert resp.status_code == 200


def test_ver_historico_exibe_candidatos(logged_in_client, db):
    h = _criar_historico()
    resp = logged_in_client.get(f'/admin/historico/{h.id}')
    assert 'João Silva' in resp.data.decode()
    assert 'Maria Lima' in resp.data.decode()


def test_ver_historico_inexistente_retorna_404(logged_in_client, db):
    resp = logged_in_client.get('/admin/historico/99999')
    assert resp.status_code == 404


# ── Exclusão ───────────────────────────────────────────────────────────────────

def test_excluir_historico_com_sucesso(logged_in_client, db):
    h = _criar_historico()
    hid = h.id
    resp = logged_in_client.post(
        f'/admin/historico/{hid}/excluir',
        follow_redirects=True,
    )

    assert resp.status_code == 200
    _db.session.expire_all()
    assert HistoricoEleicao.query.get(hid) is None


def test_excluir_historico_exibe_flash(logged_in_client, db):
    h = _criar_historico()
    resp = logged_in_client.post(
        f'/admin/historico/{h.id}/excluir',
        follow_redirects=True,
    )
    assert 'removido' in resp.data.decode().lower()


def test_excluir_historico_inexistente_retorna_404(logged_in_client, db):
    resp = logged_in_client.post('/admin/historico/99999/excluir')
    assert resp.status_code == 404


# ── Proteção de rota ───────────────────────────────────────────────────────────

def test_historico_sem_autenticacao_redireciona(client, db):
    resp = client.get('/admin/historico', follow_redirects=True)
    assert 'Acesso Administrativo' in resp.data.decode()


def test_ver_historico_sem_autenticacao_redireciona(client, db):
    h = _criar_historico()
    resp = client.get(f'/admin/historico/{h.id}', follow_redirects=True)
    assert 'Acesso Administrativo' in resp.data.decode()


def test_excluir_historico_sem_autenticacao_redireciona(client, db):
    h = _criar_historico()
    resp = client.post(f'/admin/historico/{h.id}/excluir', follow_redirects=True)
    assert 'Acesso Administrativo' in resp.data.decode()
    _db.session.expire_all()
    assert HistoricoEleicao.query.get(h.id) is not None
