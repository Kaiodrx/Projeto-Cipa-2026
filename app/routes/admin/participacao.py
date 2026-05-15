from datetime import datetime
from flask import render_template
from . import admin_bp
from ...utils import login_required
from ...services.participacao import calcular_participacao_geral


@admin_bp.route('/participacao')
@login_required
def participacao():
    dados = calcular_participacao_geral()
    now = datetime.now().strftime('%d/%m/%Y às %H:%M')
    return render_template('admin/participacao.html', dados=dados, now=now)
