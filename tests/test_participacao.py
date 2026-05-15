"""
Testes de participação eleitoral.
Cobre: cálculo por unidade, validação do mínimo de 50%, rotas do dashboard
e relatórios de participação (dashboard e nominal).
"""
from datetime import date

import pytest
from app.extensions import db as _db
from app.models import Funcionario
from app.constants import UNIDADES
from app.services.participacao import (
    calcular_participacao_unidade,
    calcular_participacao_geral,
    PERCENTUAL_MINIMO,
)

UNIDADE = UNIDADES[0]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _criar_funcionario(matricula, nome, unidade=UNIDADE, votou=False, ativo=True):
    f = Funcionario(matricula=matricula, nome=nome, unidade=unidade, votou=votou, ativo=ativo)
    _db.session.add(f)
    _db.session.commit()
    return f


# ── calcular_participacao_unidade ──────────────────────────────────────────────

def test_participacao_unidade_sem_funcionarios_retorna_zero(db):
    dados = calcular_participacao_unidade(UNIDADE)
    assert dados['total'] == 0
    assert dados['votaram'] == 0
    assert dados['percentual'] == 0.0
    assert dados['valida'] is False


def test_participacao_unidade_todos_votaram(db):
    _criar_funcionario('M001', 'Ana', votou=True)
    _criar_funcionario('M002', 'Bia', votou=True)
    dados = calcular_participacao_unidade(UNIDADE)
    assert dados['total'] == 2
    assert dados['votaram'] == 2
    assert dados['percentual'] == 100.0
    assert dados['valida'] is True


def test_participacao_unidade_metade_votou_considera_valida(db):
    _criar_funcionario('M001', 'Ana', votou=True)
    _criar_funcionario('M002', 'Bia', votou=False)
    dados = calcular_participacao_unidade(UNIDADE)
    assert dados['percentual'] == 50.0
    assert dados['valida'] is True


def test_participacao_unidade_abaixo_do_minimo(db):
    _criar_funcionario('M001', 'Ana', votou=True)
    _criar_funcionario('M002', 'Bia', votou=False)
    _criar_funcionario('M003', 'Cid', votou=False)
    dados = calcular_participacao_unidade(UNIDADE)
    assert dados['percentual'] < PERCENTUAL_MINIMO
    assert dados['valida'] is False


def test_participacao_unidade_pendentes_calculado_corretamente(db):
    _criar_funcionario('M001', 'Ana', votou=True)
    _criar_funcionario('M002', 'Bia', votou=False)
    _criar_funcionario('M003', 'Cid', votou=False)
    dados = calcular_participacao_unidade(UNIDADE)
    assert dados['pendentes'] == 2
    assert dados['total'] == 3


def test_participacao_unidade_ignora_funcionarios_inativos(db):
    _criar_funcionario('M001', 'Ana', votou=True, ativo=True)
    _criar_funcionario('M002', 'Bia', votou=False, ativo=False)  # não conta
    dados = calcular_participacao_unidade(UNIDADE)
    assert dados['total'] == 1
    assert dados['votaram'] == 1
    assert dados['percentual'] == 100.0


def test_participacao_unidade_inativo_votou_nao_entra_no_calculo(db):
    # Inativo que de alguma forma votou não deve inflar o percentual
    _criar_funcionario('M001', 'Ana', votou=False, ativo=True)
    _criar_funcionario('M002', 'Bia', votou=True, ativo=False)
    dados = calcular_participacao_unidade(UNIDADE)
    assert dados['total'] == 1
    assert dados['votaram'] == 0
    assert dados['percentual'] == 0.0


# ── calcular_participacao_geral ────────────────────────────────────────────────

def test_participacao_geral_retorna_todas_unidades(db):
    dados = calcular_participacao_geral()
    assert len(dados['por_unidade']) == len(UNIDADES)


def test_participacao_geral_consolida_totais(db):
    _criar_funcionario('M001', 'Ana', unidade=UNIDADES[0], votou=True)
    _criar_funcionario('M002', 'Bia', unidade=UNIDADES[1], votou=False)
    dados = calcular_participacao_geral()
    assert dados['total'] >= 2
    assert dados['votaram'] >= 1
    assert dados['pendentes'] >= 1


def test_participacao_geral_percentual_calculado(db):
    _criar_funcionario('M001', 'Ana', unidade=UNIDADE, votou=True)
    _criar_funcionario('M002', 'Bia', unidade=UNIDADE, votou=True)
    _criar_funcionario('M003', 'Cid', unidade=UNIDADE, votou=False)
    dados = calcular_participacao_geral()
    unidade_dados = next(d for d in dados['por_unidade'] if d['unidade'] == UNIDADE)
    assert unidade_dados['votaram'] == 2
    assert unidade_dados['total'] == 3
    assert round(unidade_dados['percentual'], 1) == round(2 / 3 * 100, 1)


# ── Rotas de participação ──────────────────────────────────────────────────────

def test_pagina_participacao_acessivel_para_admin(logged_in_client, db):
    resp = logged_in_client.get('/admin/participacao')
    assert resp.status_code == 200


def test_pagina_participacao_exibe_percentual(logged_in_client, db):
    resp = logged_in_client.get('/admin/participacao')
    assert '%' in resp.data.decode()


def test_pagina_participacao_exige_autenticacao(client, db):
    resp = client.get('/admin/participacao', follow_redirects=True)
    assert 'Acesso Administrativo' in resp.data.decode()


def test_pagina_participacao_exibe_todas_unidades(logged_in_client, db):
    resp = logged_in_client.get('/admin/participacao')
    conteudo = resp.data.decode()
    for unidade in UNIDADES:
        assert unidade in conteudo


# ── Relatório dashboard ────────────────────────────────────────────────────────

def test_relatorio_dashboard_acessivel(logged_in_client, db):
    resp = logged_in_client.get('/admin/relatorio/participacao/dashboard')
    assert resp.status_code == 200


def test_relatorio_dashboard_exige_autenticacao(client, db):
    resp = client.get('/admin/relatorio/participacao/dashboard', follow_redirects=True)
    assert 'Acesso Administrativo' in resp.data.decode()


def test_relatorio_dashboard_exibe_unidades(logged_in_client, db):
    resp = logged_in_client.get('/admin/relatorio/participacao/dashboard')
    conteudo = resp.data.decode()
    for unidade in UNIDADES:
        assert unidade in conteudo


def test_relatorio_dashboard_exibe_percentuais(logged_in_client, db):
    resp = logged_in_client.get('/admin/relatorio/participacao/dashboard')
    assert '%' in resp.data.decode()


def test_relatorio_dashboard_dados_corretos(logged_in_client, db):
    _criar_funcionario('M001', 'Ana', unidade=UNIDADE, votou=True)
    _criar_funcionario('M002', 'Bia', unidade=UNIDADE, votou=False)
    resp = logged_in_client.get('/admin/relatorio/participacao/dashboard')
    conteudo = resp.data.decode()
    assert '50.0%' in conteudo


# ── Relatório nominal ──────────────────────────────────────────────────────────

def test_relatorio_nominal_acessivel(logged_in_client, db):
    resp = logged_in_client.get('/admin/relatorio/participacao/nominal')
    assert resp.status_code == 200


def test_relatorio_nominal_exige_autenticacao(client, db):
    resp = client.get('/admin/relatorio/participacao/nominal', follow_redirects=True)
    assert 'Acesso Administrativo' in resp.data.decode()


def test_relatorio_nominal_exibe_funcionarios(logged_in_client, db):
    _criar_funcionario('M001', 'Ana Silva', unidade=UNIDADE)
    resp = logged_in_client.get('/admin/relatorio/participacao/nominal')
    assert 'Ana Silva' in resp.data.decode()


def test_relatorio_nominal_filtra_por_unidade(logged_in_client, db):
    _criar_funcionario('M001', 'Ana Silva', unidade=UNIDADE, votou=True)
    _criar_funcionario('M002', 'Carlos Melo', unidade=UNIDADES[1], votou=False)
    resp = logged_in_client.get(f'/admin/relatorio/participacao/nominal?unidade={UNIDADE}')
    conteudo = resp.data.decode()
    assert 'Ana Silva' in conteudo
    assert 'Carlos Melo' not in conteudo


def test_relatorio_nominal_unidade_invalida_retorna_404(logged_in_client, db):
    resp = logged_in_client.get('/admin/relatorio/participacao/nominal?unidade=UNIDADE_INEXISTENTE')
    assert resp.status_code == 404


def test_relatorio_nominal_exibe_status_votou(logged_in_client, db):
    _criar_funcionario('M001', 'Ana', unidade=UNIDADE, votou=True)
    _criar_funcionario('M002', 'Bia', unidade=UNIDADE, votou=False)
    resp = logged_in_client.get(f'/admin/relatorio/participacao/nominal?unidade={UNIDADE}')
    conteudo = resp.data.decode()
    assert 'Votou' in conteudo
    assert 'Pendente' in conteudo


def test_relatorio_nominal_exclui_funcionarios_inativos(logged_in_client, db):
    _criar_funcionario('M001', 'Ativo Sim', unidade=UNIDADE, ativo=True)
    _criar_funcionario('M002', 'Inativo Nao', unidade=UNIDADE, ativo=False)
    resp = logged_in_client.get(f'/admin/relatorio/participacao/nominal?unidade={UNIDADE}')
    conteudo = resp.data.decode()
    assert 'Ativo Sim' in conteudo
    assert 'Inativo Nao' not in conteudo
