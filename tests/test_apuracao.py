"""
Testes do serviço de apuração da eleição por unidade.
Cobre: ordenação por votos, desempate por admissão, desempate por nome,
eleição com dimensionamento, caso sem candidatos.
"""
from datetime import date
import pytest
from app.extensions import db as _db
from app.models import Candidato, Funcionario, Eleicao, Voto
from app.constants import UNIDADES
from app.services.apuracao import apurar_eleicao

UNIDADE = UNIDADES[0]


def _criar_candidato(nome, unidade=UNIDADE, funcionario_id=None):
    c = Candidato(nome=nome, cargo='', unidade=unidade, funcionario_id=funcionario_id)
    _db.session.add(c)
    _db.session.flush()
    return c


def _criar_funcionario(matricula, nome, admissao=None, unidade=UNIDADE):
    f = Funcionario(
        matricula=matricula, nome=nome, unidade=unidade, votou=False, ativo=True,
        data_admissao=admissao,
    )
    _db.session.add(f)
    _db.session.flush()
    return f


def _votar(candidato_id, n=1):
    for _ in range(n):
        _db.session.add(Voto(candidato_id=candidato_id))
    _db.session.flush()


# ── Ordenação básica por votos ─────────────────────────────────────────────────

def test_candidatos_ordenados_por_votos(db):
    c1 = _criar_candidato('Ana')
    c2 = _criar_candidato('Carlos')
    c3 = _criar_candidato('Beatriz')
    _votar(c1.id, 5)
    _votar(c2.id, 3)
    _votar(c3.id, 7)
    _db.session.commit()

    r = apurar_eleicao(UNIDADE)
    nomes = [item['candidato'].nome for item in r['candidatos']]
    assert nomes == ['Beatriz', 'Ana', 'Carlos']


def test_totais_de_votos(db):
    c1 = _criar_candidato('Ana')
    c2 = _criar_candidato('Bia')
    _votar(c1.id, 4)
    _votar(c2.id, 6)
    _db.session.commit()

    r = apurar_eleicao(UNIDADE)
    assert r['total_votos'] == 10


# ── Desempate por data de admissão ─────────────────────────────────────────────

def test_desempate_por_data_admissao(db):
    # Mesmo número de votos: mais antigo deve aparecer primeiro
    f_antigo = _criar_funcionario('M001', 'Carlos', admissao=date(2010, 1, 1))
    f_novo = _criar_funcionario('M002', 'Ana', admissao=date(2020, 1, 1))
    c_antigo = _criar_candidato('Carlos', funcionario_id=f_antigo.id)
    c_novo = _criar_candidato('Ana', funcionario_id=f_novo.id)
    _votar(c_antigo.id, 3)
    _votar(c_novo.id, 3)
    _db.session.commit()

    r = apurar_eleicao(UNIDADE)
    assert r['candidatos'][0]['candidato'].nome == 'Carlos'
    assert r['candidatos'][1]['candidato'].nome == 'Ana'


def test_desempate_por_data_admissao_marca_flag(db):
    f1 = _criar_funcionario('M001', 'Alice', admissao=date(2015, 1, 1))
    f2 = _criar_funcionario('M002', 'Bruno', admissao=date(2018, 1, 1))
    c1 = _criar_candidato('Alice', funcionario_id=f1.id)
    c2 = _criar_candidato('Bruno', funcionario_id=f2.id)
    _votar(c1.id, 2)
    _votar(c2.id, 2)
    _db.session.commit()

    r = apurar_eleicao(UNIDADE)
    assert r['candidatos'][0]['desempate_aplicado'] is True
    assert r['candidatos'][1]['desempate_aplicado'] is True


# ── Desempate por nome (sem data de admissão) ──────────────────────────────────

def test_desempate_por_nome_quando_sem_admissao(db):
    # Sem funcionário vinculado → sem data de admissão → usa nome
    c1 = _criar_candidato('Zara')
    c2 = _criar_candidato('Ana')
    _votar(c1.id, 3)
    _votar(c2.id, 3)
    _db.session.commit()

    r = apurar_eleicao(UNIDADE)
    # 'Ana' vem antes de 'Zara' alfabeticamente
    assert r['candidatos'][0]['candidato'].nome == 'Ana'
    assert r['candidatos'][1]['candidato'].nome == 'Zara'


# ── Situação dos eleitos ───────────────────────────────────────────────────────

def test_situacao_titular_suplente_nao_eleito(db):
    # Cria 3 funcionários ativos para dimensionamento: 30 func → 1T, 1S
    for i in range(28):
        _db.session.add(Funcionario(
            matricula=f'X{i:03d}', nome=f'Func {i}', unidade=UNIDADE, ativo=True
        ))
    c1 = _criar_candidato('Primeiro')
    c2 = _criar_candidato('Segundo')
    c3 = _criar_candidato('Terceiro')
    _votar(c1.id, 10)
    _votar(c2.id, 5)
    _votar(c3.id, 2)
    _db.session.commit()

    r = apurar_eleicao(UNIDADE)
    situacoes = [item['situacao'] for item in r['candidatos']]
    assert situacoes[0] == 'Titular'
    assert situacoes[1] == 'Suplente'
    assert situacoes[2] == 'Não eleito'


# ── Caso sem candidatos ────────────────────────────────────────────────────────

def test_sem_candidatos_retorna_lista_vazia(db):
    r = apurar_eleicao(UNIDADE)
    assert r['candidatos'] == []
    assert r['total_votos'] == 0


# ── Percentuais ───────────────────────────────────────────────────────────────

def test_percentuais_somam_100(db):
    c1 = _criar_candidato('A')
    c2 = _criar_candidato('B')
    _votar(c1.id, 3)
    _votar(c2.id, 7)
    _db.session.commit()

    r = apurar_eleicao(UNIDADE)
    total_pct = sum(item['pct'] for item in r['candidatos'])
    assert abs(total_pct - 100.0) < 0.2  # tolerância para arredondamento


# ── Rota de apuração ──────────────────────────────────────────────────────────

def test_rota_apuracao_retorna_200(logged_in_client, db):
    resp = logged_in_client.get(f'/admin/eleicao/{UNIDADE}/apuracao')
    assert resp.status_code == 200


def test_rota_apuracao_unidade_invalida_retorna_404(logged_in_client, db):
    resp = logged_in_client.get('/admin/eleicao/UNIDADE_FALSA/apuracao')
    assert resp.status_code == 404


def test_rota_apuracao_sem_autenticacao_redireciona(client, db):
    resp = client.get(f'/admin/eleicao/{UNIDADE}/apuracao', follow_redirects=True)
    assert 'Acesso Administrativo' in resp.data.decode()
