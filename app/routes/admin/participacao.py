from datetime import datetime
from flask import render_template
from . import admin_bp
from ...models import Funcionario
from ...constants import UNIDADES
from ...utils import login_required


@admin_bp.route('/participacao')
@login_required
def participacao():
    dados_por_unidade = {}
    total_votaram = 0
    total_funcionarios = 0
    for unidade in UNIDADES:
        todos = Funcionario.query.filter_by(unidade=unidade).all()
        votaram = [f for f in todos if f.votou]
        pendentes = [f for f in todos if not f.votou]
        dados_por_unidade[unidade] = {
            'total': len(todos),
            'votaram': votaram,
            'pendentes': pendentes,
        }
        total_votaram += len(votaram)
        total_funcionarios += len(todos)
    now = datetime.now().strftime('%d/%m/%Y às %H:%M')
    return render_template('admin/participacao.html',
                           dados_por_unidade=dados_por_unidade,
                           total_funcionarios=total_funcionarios,
                           total_votaram=total_votaram,
                           total_pendentes=total_funcionarios - total_votaram,
                           unidades=UNIDADES,
                           now=now)
