from flask import render_template, abort
from . import admin_bp
from ...constants import UNIDADES
from ...utils import login_required
from ...services.apuracao import apurar_eleicao


@admin_bp.route('/eleicao/<unidade>/apuracao')
@login_required
def apuracao_unidade(unidade):
    if unidade not in UNIDADES:
        abort(404)
    resultado = apurar_eleicao(unidade)
    return render_template('admin/apuracao.html', resultado=resultado)
