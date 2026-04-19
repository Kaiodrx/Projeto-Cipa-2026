"""
Testes do fluxo público de votação.
Cobre: voto válido, voto duplicado, eleição fechada, exibição de resultado.
"""
import pytest
from app.extensions import db as _db
from app.models import Funcionario, Voto
from app.constants import UNIDADES

UNIDADE = UNIDADES[0]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _fazer_login_votacao(client, matricula, unidade):
    return client.post('/votacao', data={
        'matricula': matricula,
        'unidade': unidade,
    }, follow_redirects=False)


# ── Login de votação ───────────────────────────────────────────────────────────

def test_login_votacao_com_matricula_invalida_exibe_erro(client, db, eleicao_aberta):
    resp = client.post('/votacao', data={
        'matricula': 'INEXISTENTE',
        'unidade': UNIDADE,
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert 'não encontrada' in resp.data.decode()


def test_login_votacao_com_unidade_incorreta_exibe_erro(client, db, funcionario, eleicao_aberta):
    outra_unidade = UNIDADES[1]
    resp = client.post('/votacao', data={
        'matricula': funcionario.matricula,
        'unidade': outra_unidade,
    }, follow_redirects=True)

    assert 'Unidade incorreta' in resp.data.decode()


def test_login_votacao_com_eleicao_fechada_exibe_aviso(client, db, funcionario):
    # eleicao_aberta NÃO é usada — a eleição permanece fechada
    resp = client.post('/votacao', data={
        'matricula': funcionario.matricula,
        'unidade': UNIDADE,
    }, follow_redirects=True)

    assert 'não está aberta' in resp.data.decode()


def test_login_votacao_com_sucesso_redireciona_para_votar(client, db, funcionario, eleicao_aberta):
    resp = _fazer_login_votacao(client, funcionario.matricula, UNIDADE)
    assert resp.status_code == 302
    assert '/votar' in resp.headers['Location']


# ── Registro de voto ───────────────────────────────────────────────────────────

def test_voto_valido_registrado_com_sucesso(client, db, funcionario, candidato, eleicao_aberta):
    _fazer_login_votacao(client, funcionario.matricula, UNIDADE)

    resp = client.post('/votar', data={
        'candidato_id': candidato.id,
    }, follow_redirects=True)

    assert resp.status_code == 200
    _db.session.expire_all()
    assert Voto.query.filter_by(candidato_id=candidato.id).count() == 1
    assert Funcionario.query.get(funcionario.id).votou is True


def test_voto_valido_redireciona_para_confirmacao(client, db, funcionario, candidato, eleicao_aberta):
    _fazer_login_votacao(client, funcionario.matricula, UNIDADE)

    resp = client.post('/votar', data={'candidato_id': candidato.id})
    assert resp.status_code == 302
    assert '/confirmacao' in resp.headers['Location']


def test_voto_duplicado_exibe_aviso_e_nao_registra(client, db, funcionario, candidato, eleicao_aberta):
    # Marca o funcionário como já tendo votado
    funcionario.votou = True
    _db.session.commit()

    resp = client.post('/votacao', data={
        'matricula': funcionario.matricula,
        'unidade': UNIDADE,
    }, follow_redirects=True)

    assert 'já votou' in resp.data.decode()
    assert Voto.query.count() == 0


def test_votar_sem_sessao_redireciona_para_login(client, db):
    resp = client.post('/votar', data={'candidato_id': '1'})
    assert resp.status_code == 302
    assert '/votacao' in resp.headers['Location']


def test_votar_com_eleicao_fechada_redireciona(client, db, funcionario, candidato, eleicao_aberta):
    _fazer_login_votacao(client, funcionario.matricula, UNIDADE)

    # Fecha a eleição depois de autenticado
    eleicao_aberta.status = 'fechada'
    _db.session.commit()

    resp = client.post('/votar', data={'candidato_id': candidato.id}, follow_redirects=True)
    assert 'não está aberta' in resp.data.decode()
    assert Voto.query.count() == 0


# ── Resultado ──────────────────────────────────────────────────────────────────

def test_resultado_exibido_para_admin_autenticado(logged_in_client, db):
    resp = logged_in_client.get('/admin/resultado')
    assert resp.status_code == 200
    assert UNIDADE in resp.data.decode()


def test_resultado_sem_autenticacao_redireciona(client, db):
    resp = client.get('/admin/resultado', follow_redirects=True)
    assert 'Acesso Administrativo' in resp.data.decode()


def test_resultado_contabiliza_votos_corretamente(logged_in_client, db, funcionario, candidato, eleicao_aberta):
    # Registra um voto diretamente via ORM
    _db.session.add(Voto(candidato_id=candidato.id))
    funcionario.votou = True
    _db.session.commit()

    resp = logged_in_client.get('/admin/resultado')
    assert candidato.nome in resp.data.decode()
