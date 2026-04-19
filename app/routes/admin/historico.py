import json
from flask import render_template, redirect, url_for, flash
from . import admin_bp
from ...extensions import db
from ...models import HistoricoEleicao
from ...utils import login_required


@admin_bp.route('/historico')
@login_required
def historico():
    registros_raw = HistoricoEleicao.query.order_by(HistoricoEleicao.data.desc()).all()
    registros = []
    for r in registros_raw:
        snap = json.loads(r.dados)
        vencedores = []
        for u in snap.get('unidades', []):
            cands = u.get('candidatos', [])
            if cands and cands[0]['votos'] > 0:
                vencedores.append({'unidade': u['unidade'], 'nome': cands[0]['nome'], 'votos': cands[0]['votos']})
        registros.append({
            'registro': r,
            'total_geral': snap.get('total_geral', 0),
            'vencedores': vencedores,
        })
    return render_template('admin/historico.html', registros=registros)


@admin_bp.route('/historico/<int:id>')
@login_required
def ver_historico(id):
    registro = HistoricoEleicao.query.get_or_404(id)
    snapshot = json.loads(registro.dados)
    return render_template('admin/historico_detalhe.html', registro=registro, snapshot=snapshot)


@admin_bp.route('/historico/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_historico(id):
    registro = HistoricoEleicao.query.get_or_404(id)
    db.session.delete(registro)
    db.session.commit()
    flash('Registro removido do histórico.', 'warning')
    return redirect(url_for('admin.historico'))
