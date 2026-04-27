from flask import render_template, request, redirect, url_for, flash
from . import admin_bp
from ...extensions import db
from ...models import Candidato, Funcionario, Eleicao
from ...constants import UNIDADES
from ...utils import login_required


@admin_bp.route('/eleicao')
@login_required
def gerenciar_eleicao():
    status_filtro = request.args.get('status', '')
    eleicoes = {e.unidade: e for e in Eleicao.query.all()}
    total_abertas = sum(1 for e in eleicoes.values() if e.status == 'aberta')

    if status_filtro == 'aberta':
        unidades_visiveis = [u for u in UNIDADES if eleicoes.get(u) and eleicoes[u].status == 'aberta']
    elif status_filtro == 'fechada':
        unidades_visiveis = [u for u in UNIDADES if not eleicoes.get(u) or eleicoes[u].status != 'aberta']
    else:
        unidades_visiveis = UNIDADES

    candidatos_por_unidade = {u: Candidato.query.filter_by(unidade=u).all() for u in UNIDADES}
    funcionarios_por_unidade = {u: Funcionario.query.filter_by(unidade=u).count() for u in UNIDADES}
    return render_template(
        'admin/eleicao.html',
        eleicoes=eleicoes,
        candidatos_por_unidade=candidatos_por_unidade,
        funcionarios_por_unidade=funcionarios_por_unidade,
        unidades=unidades_visiveis,
        total_unidades=len(UNIDADES),
        total_abertas=total_abertas,
        status_filtro=status_filtro,
    )


@admin_bp.route('/eleicao/abrir-todas')
@login_required
def abrir_todas():
    for e in Eleicao.query.all():
        e.status = 'aberta'
    db.session.commit()
    flash('Todas as unidades foram abertas!', 'success')
    return redirect(url_for('admin.gerenciar_eleicao'))


@admin_bp.route('/eleicao/fechar-todas')
@login_required
def fechar_todas():
    for e in Eleicao.query.all():
        e.status = 'fechada'
    db.session.commit()
    flash('Todas as unidades foram encerradas.', 'warning')
    return redirect(url_for('admin.gerenciar_eleicao'))


@admin_bp.route('/eleicao/abrir', methods=['POST'])
@login_required
def abrir_eleicao():
    unidade = request.form.get('unidade', '').strip()
    eleicao = Eleicao.query.filter_by(unidade=unidade).first_or_404()
    eleicao.status = 'aberta'
    db.session.commit()
    flash(f'{unidade} — eleição aberta!', 'success')
    return redirect(url_for('admin.gerenciar_eleicao'))


@admin_bp.route('/eleicao/fechar', methods=['POST'])
@login_required
def fechar_eleicao():
    unidade = request.form.get('unidade', '').strip()
    eleicao = Eleicao.query.filter_by(unidade=unidade).first_or_404()
    eleicao.status = 'fechada'
    db.session.commit()
    flash(f'{unidade} — eleição encerrada.', 'warning')
    return redirect(url_for('admin.gerenciar_eleicao'))
