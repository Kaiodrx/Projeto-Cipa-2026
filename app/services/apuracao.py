"""
Apuração automática da eleição da CIPA por unidade.

Critério de desempate (documentado e aplicado de forma consistente):
  1. Mais votos — primário (decrescente)
  2. Data de admissão mais antiga — secundário (crescente); funcionário mais antigo tem prioridade
  3. Nome em ordem alfabética — terciário/final (crescente); determinístico e auditável

O critério de desempate só é aplicado quando há empate em votos.
A data de admissão é obtida via vínculo candidato → funcionario_id.
Se o candidato não estiver vinculado a um funcionário, ele é tratado como sem data
(aparece no final do grupo empatado, antes de ser resolvido pelo nome).
"""
from datetime import date as _date
from ..models import Candidato, Funcionario, Eleicao
from .dimensionamento import calcular_dimensionamento

_DATA_MAXIMA = _date(9999, 12, 31)  # Sentinela: candidato sem data vai para o final do grupo


def apurar_eleicao(unidade: str) -> dict:
    """
    Calcula o resultado completo da eleição para uma unidade.

    Pode ser chamado com eleição aberta (resultado parcial) ou fechada (resultado final).
    Todos os cálculos são feitos em tempo real com base nos votos atuais do banco.

    Returns:
        dict com: unidade, eleicao, candidatos (lista ordenada com situação),
        totais de eleitores/votantes/não-votantes, percentual de participação,
        n_titulares, n_suplentes, dimensionamento.
    """
    candidatos = Candidato.query.filter_by(unidade=unidade).all()

    dados = []
    for c in candidatos:
        votos = len(c.votos)
        admissao = _obter_data_admissao(c)
        dados.append({'candidato': c, 'votos': votos, 'data_admissao': admissao})

    # Ordenação com três critérios de desempate
    dados.sort(key=lambda d: (
        -d['votos'],
        d['data_admissao'] or _DATA_MAXIMA,
        d['candidato'].nome,
    ))

    total_eleitores = Funcionario.query.filter_by(unidade=unidade, ativo=True).count()
    total_votantes = Funcionario.query.filter_by(unidade=unidade, votou=True).count()
    total_votos = sum(d['votos'] for d in dados)
    dim = calcular_dimensionamento(total_eleitores)
    n_t = dim['titulares']
    n_s = dim['suplentes']

    resultado = []
    for i, d in enumerate(dados):
        pos = i + 1
        votos = d['votos']
        pct = round(votos / total_votos * 100, 1) if total_votos > 0 else 0.0

        if pos <= n_t:
            situacao = 'Titular'
        elif pos <= n_t + n_s:
            situacao = 'Suplente'
        else:
            situacao = 'Não eleito'

        resultado.append({
            'posicao': pos,
            'candidato': d['candidato'],
            'votos': votos,
            'pct': pct,
            'situacao': situacao,
            'data_admissao': d['data_admissao'],
            'desempate_aplicado': False,
        })

    _marcar_desempates(resultado)

    eleicao = Eleicao.query.filter_by(unidade=unidade).first()
    pct_part = round(total_votantes / total_eleitores * 100, 1) if total_eleitores > 0 else 0.0

    return {
        'unidade': unidade,
        'eleicao': eleicao,
        'candidatos': resultado,
        'total_votos': total_votos,
        'total_eleitores': total_eleitores,
        'total_votantes': total_votantes,
        'total_nao_votantes': total_eleitores - total_votantes,
        'pct_participacao': pct_part,
        'n_titulares': n_t,
        'n_suplentes': n_s,
        'dimensionamento': dim,
    }


def _obter_data_admissao(candidato: Candidato):
    """Retorna a data de admissão do funcionário vinculado ao candidato, ou None."""
    if candidato.funcionario_id:
        func = Funcionario.query.get(candidato.funcionario_id)
        if func:
            return func.data_admissao
    return None


def _marcar_desempates(resultado: list) -> None:
    """Marca candidatos onde houve empate em votos (desempate por admissão/nome foi aplicado)."""
    n = len(resultado)
    for i in range(n):
        resultado[i].setdefault('desempate_aplicado', False)

    for i in range(n - 1):
        if resultado[i]['votos'] == resultado[i + 1]['votos']:
            resultado[i]['desempate_aplicado'] = True
            resultado[i + 1]['desempate_aplicado'] = True
