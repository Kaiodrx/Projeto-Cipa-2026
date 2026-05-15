"""
Cálculo de participação eleitoral por unidade.

Isolado aqui para que rotas e templates não carreguem lógica de negócio.
"""
from ..models import Funcionario
from ..constants import UNIDADES

PERCENTUAL_MINIMO = 50.0


def calcular_participacao_unidade(unidade: str) -> dict:
    """
    Retorna estatísticas de participação de uma única unidade.

    Usa apenas funcionários ativos como base de cálculo (elegíveis).
    """
    total = Funcionario.query.filter_by(unidade=unidade, ativo=True).count()
    votaram = Funcionario.query.filter_by(unidade=unidade, ativo=True, votou=True).count()
    percentual = round(votaram / total * 100, 1) if total > 0 else 0.0
    return {
        'unidade': unidade,
        'total': total,
        'votaram': votaram,
        'pendentes': total - votaram,
        'percentual': percentual,
        'valida': percentual >= PERCENTUAL_MINIMO,
    }


def calcular_participacao_geral() -> dict:
    """
    Retorna participação consolidada de todas as unidades.
    """
    por_unidade = [calcular_participacao_unidade(u) for u in UNIDADES]
    total = sum(d['total'] for d in por_unidade)
    votaram = sum(d['votaram'] for d in por_unidade)
    percentual = round(votaram / total * 100, 1) if total > 0 else 0.0
    return {
        'por_unidade': por_unidade,
        'total': total,
        'votaram': votaram,
        'pendentes': total - votaram,
        'percentual': percentual,
        'valida': percentual >= PERCENTUAL_MINIMO,
    }
