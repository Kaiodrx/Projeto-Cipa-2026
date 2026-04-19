from flask import render_template
from . import admin_bp
from ...models import Candidato, Funcionario, Voto, Eleicao
from ...constants import UNIDADES
from ...utils import login_required


@admin_bp.route('')
@login_required
def dashboard():
    eleicoes = {e.unidade: e for e in Eleicao.query.all()}
    abertas = sum(1 for e in eleicoes.values() if e.status == 'aberta')
    andamento = []
    for unidade in UNIDADES:
        eleicao = eleicoes.get(unidade)
        if not eleicao or eleicao.status != 'aberta':
            continue
        total_func = Funcionario.query.filter_by(unidade=unidade).count()
        votaram = Funcionario.query.filter_by(unidade=unidade, votou=True).count()
        votos = Voto.query.join(Candidato).filter(Candidato.unidade == unidade).count()
        pct = round(votaram / total_func * 100, 1) if total_func > 0 else 0
        andamento.append({
            'unidade': unidade,
            'votaram': votaram,
            'total': total_func,
            'votos': votos,
            'pct': pct,
        })
    return render_template('admin/dashboard.html',
                           total_candidatos=Candidato.query.count(),
                           total_funcionarios=Funcionario.query.count(),
                           total_votos=Voto.query.count(),
                           unidades_abertas=abertas,
                           total_unidades=len(UNIDADES),
                           andamento=andamento,
                           unidades=UNIDADES)
