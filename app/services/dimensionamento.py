"""
Dimensionamento da CIPA — Grau de Risco 3 (NR-5, Tabela I)

Fonte: Norma Regulamentadora NR-5, Tabela I, coluna Grau de Risco 3.

Regra para acima de 10.000 funcionários:
  A partir de 10.001, acrescenta-se 2 titulares e 2 suplentes por grupo adicional
  de 2.500 funcionários acima de 10.000, contando grupos completos (ceiling).

  Exemplos:
    10.001 a 12.500 → 1 grupo → 14 titulares, 10 suplentes
    12.501 a 15.000 → 2 grupos → 16 titulares, 12 suplentes
    15.001 a 17.500 → 3 grupos → 18 titulares, 14 suplentes
"""
import math

# (min_func, max_func, titulares, suplentes)
_TABELA_GR3 = [
    (0,      19,    0,  0),
    (20,     29,    1,  1),
    (30,     50,    1,  1),
    (51,     80,    2,  1),
    (81,    100,    2,  1),
    (101,   120,    2,  1),
    (121,   140,    3,  2),
    (141,   300,    4,  2),
    (301,   500,    5,  4),
    (501,  1000,    6,  4),
    (1001, 2500,    8,  6),
    (2501, 5000,   10,  8),
    (5001, 10000,  12,  8),
]

_LIMITE_TABELA = 10_000
_BASE_TITULARES = 12
_BASE_SUPLENTES = 8
_TAMANHO_GRUPO = 2_500


def calcular_dimensionamento(num_funcionarios: int) -> dict:
    """
    Calcula o dimensionamento da CIPA para grau de risco 3.

    Args:
        num_funcionarios: número de funcionários no estabelecimento (eleitores ativos).

    Returns:
        dict com chaves 'titulares' (int) e 'suplentes' (int).
    """
    n = max(0, int(num_funcionarios))

    if n <= _LIMITE_TABELA:
        for min_f, max_f, titulares, suplentes in _TABELA_GR3:
            if min_f <= n <= max_f:
                return {'titulares': titulares, 'suplentes': suplentes}
        return {'titulares': 0, 'suplentes': 0}

    # Acima de 10.000: cada grupo completo de 2.500 adiciona 2T e 2S.
    # math.ceil garante que qualquer fração de grupo já conta como um grupo adicional.
    grupos = math.ceil((n - _LIMITE_TABELA) / _TAMANHO_GRUPO)
    return {
        'titulares': _BASE_TITULARES + grupos * 2,
        'suplentes': _BASE_SUPLENTES + grupos * 2,
    }
