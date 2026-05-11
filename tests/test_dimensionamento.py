"""
Testes do serviço de dimensionamento da CIPA (Grau de Risco 3).
Cobre: faixas da tabela, limites exatos, acima de 10.000, entradas inválidas.
"""
import pytest
from app.services.dimensionamento import calcular_dimensionamento


# ── Faixas da tabela NR-5 GR3 ─────────────────────────────────────────────────

@pytest.mark.parametrize('n, titulares, suplentes', [
    (0,     0,  0),
    (19,    0,  0),
    (20,    1,  1),
    (25,    1,  1),
    (29,    1,  1),
    (30,    1,  1),
    (50,    1,  1),
    (51,    2,  1),
    (80,    2,  1),
    (81,    2,  1),
    (100,   2,  1),
    (101,   2,  1),
    (120,   2,  1),
    (121,   3,  2),
    (140,   3,  2),
    (141,   4,  2),
    (300,   4,  2),
    (301,   5,  4),
    (500,   5,  4),
    (501,   6,  4),
    (1000,  6,  4),
    (1001,  8,  6),
    (2500,  8,  6),
    (2501, 10,  8),
    (5000, 10,  8),
    (5001, 12,  8),
    (10000, 12, 8),
])
def test_faixas_tabela(n, titulares, suplentes):
    resultado = calcular_dimensionamento(n)
    assert resultado['titulares'] == titulares
    assert resultado['suplentes'] == suplentes


# ── Acima de 10.000 ────────────────────────────────────────────────────────────

def test_acima_10000_primeiro_grupo():
    # 10.001 → 1 grupo adicional → 14T, 10S
    r = calcular_dimensionamento(10001)
    assert r['titulares'] == 14
    assert r['suplentes'] == 10


def test_acima_10000_limite_primeiro_grupo():
    # 12.500 → 1 grupo completo → 14T, 10S
    r = calcular_dimensionamento(12500)
    assert r['titulares'] == 14
    assert r['suplentes'] == 10


def test_acima_10000_segundo_grupo():
    # 12.501 → 2 grupos → 16T, 12S
    r = calcular_dimensionamento(12501)
    assert r['titulares'] == 16
    assert r['suplentes'] == 12


def test_acima_10000_terceiro_grupo():
    # 15.001 → 3 grupos → 18T, 14S
    r = calcular_dimensionamento(15001)
    assert r['titulares'] == 18
    assert r['suplentes'] == 14


# ── Entradas inválidas / limites ───────────────────────────────────────────────

def test_entrada_zero():
    r = calcular_dimensionamento(0)
    assert r['titulares'] == 0
    assert r['suplentes'] == 0


def test_entrada_negativa_tratada_como_zero():
    r = calcular_dimensionamento(-5)
    assert r['titulares'] == 0
    assert r['suplentes'] == 0


def test_retorna_dict_com_chaves_corretas():
    r = calcular_dimensionamento(100)
    assert 'titulares' in r
    assert 'suplentes' in r


def test_valores_sao_inteiros():
    r = calcular_dimensionamento(500)
    assert isinstance(r['titulares'], int)
    assert isinstance(r['suplentes'], int)
