from datetime import datetime
from flask import render_template, redirect, url_for, flash, abort
from . import admin_bp
from ...extensions import db
from ...models import Candidato, Funcionario, Voto, Eleicao
from ...constants import UNIDADES
from ...utils import login_required
from ...services.dimensionamento import calcular_dimensionamento


@admin_bp.route('/eleicao')
@login_required
def gerenciar_eleicao():
    status_filtro = __import__('flask').request.args.get('status', '')
    eleicoes = {e.unidade: e for e in Eleicao.query.all()}
    total_abertas = sum(1 for e in eleicoes.values() if e.status == 'aberta')

    if status_filtro == 'aberta':
        unidades_visiveis = [u for u in UNIDADES if eleicoes.get(u) and eleicoes[u].status == 'aberta']
    elif status_filtro == 'fechada':
        unidades_visiveis = [u for u in UNIDADES if not eleicoes.get(u) or eleicoes[u].status != 'aberta']
    else:
        unidades_visiveis = list(UNIDADES)

    eleitores_por_unidade = {u: Funcionario.query.filter_by(unidade=u, ativo=True).count() for u in UNIDADES}
    funcionarios_por_unidade = {u: Funcionario.query.filter_by(unidade=u).count() for u in UNIDADES}
    candidatos_por_unidade = {u: Candidato.query.filter_by(unidade=u).count() for u in UNIDADES}
    dimensionamento_por_unidade = {u: calcular_dimensionamento(eleitores_por_unidade[u]) for u in UNIDADES}
    votos_por_unidade = {
        u: Voto.query.join(Candidato).filter(Candidato.unidade == u).count()
        for u in UNIDADES
    }

    return render_template(
        'admin/eleicao.html',
        eleicoes=eleicoes,
        eleitores_por_unidade=eleitores_por_unidade,
        funcionarios_por_unidade=funcionarios_por_unidade,
        candidatos_por_unidade=candidatos_por_unidade,
        dimensionamento_por_unidade=dimensionamento_por_unidade,
        votos_por_unidade=votos_por_unidade,
        unidades=unidades_visiveis,
        total_unidades=len(UNIDADES),
        total_abertas=total_abertas,
        status_filtro=status_filtro,
    )


@admin_bp.route('/eleicao/abrir-todas')
@login_required
def abrir_todas():
    now = datetime.utcnow()
    for e in Eleicao.query.all():
        if e.status != 'aberta':
            e.status = 'aberta'
            e.data_abertura = now
    db.session.commit()
    flash('Todas as unidades foram abertas!', 'success')
    return redirect(url_for('admin.gerenciar_eleicao'))


@admin_bp.route('/eleicao/fechar-todas')
@login_required
def fechar_todas():
    now = datetime.utcnow()
    for e in Eleicao.query.all():
        if e.status == 'aberta':
            e.status = 'fechada'
            e.data_encerramento = now
    db.session.commit()
    flash('Todas as unidades foram encerradas.', 'warning')
    return redirect(url_for('admin.gerenciar_eleicao'))


@admin_bp.route('/eleicao/<unidade>/abrir')
@login_required
def abrir_eleicao(unidade):
    eleicao = Eleicao.query.filter_by(unidade=unidade).first_or_404()
    eleicao.status = 'aberta'
    eleicao.data_abertura = datetime.utcnow()
    db.session.commit()
    flash(f'{unidade} — eleição aberta!', 'success')
    return redirect(url_for('admin.gerenciar_eleicao'))


@admin_bp.route('/eleicao/<unidade>/fechar')
@login_required
def fechar_eleicao(unidade):
    eleicao = Eleicao.query.filter_by(unidade=unidade).first_or_404()
    eleicao.status = 'fechada'
    eleicao.data_encerramento = datetime.utcnow()
    db.session.commit()
    flash(f'{unidade} — eleição encerrada.', 'warning')
    return redirect(url_for('admin.gerenciar_eleicao'))
