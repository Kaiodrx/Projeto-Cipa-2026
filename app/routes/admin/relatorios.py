from datetime import datetime
from flask import render_template, abort, request
from . import admin_bp
from ...constants import UNIDADES
from ...utils import login_required
from ...models import Candidato, Funcionario, Eleicao, Voto
from ...services.apuracao import apurar_eleicao
from ...services.dimensionamento import calcular_dimensionamento
from ...services.participacao import calcular_participacao_geral, calcular_participacao_unidade


def _get_unidade_or_404(unidade):
    if unidade not in UNIDADES:
        abort(404)
    return unidade


@admin_bp.route('/eleicao/<unidade>/relatorios')
@login_required
def relatorios_unidade(unidade):
    _get_unidade_or_404(unidade)
    eleicao = Eleicao.query.filter_by(unidade=unidade).first_or_404()
    total_eleitores = Funcionario.query.filter_by(unidade=unidade, ativo=True).count()
    total_candidatos = Candidato.query.filter_by(unidade=unidade).count()
    dim = calcular_dimensionamento(total_eleitores)
    return render_template(
        'admin/relatorios_index.html',
        unidade=unidade,
        eleicao=eleicao,
        total_eleitores=total_eleitores,
        total_candidatos=total_candidatos,
        dimensionamento=dim,
    )


@admin_bp.route('/eleicao/<unidade>/relatorio/zeresima')
@login_required
def zeresima(unidade):
    _get_unidade_or_404(unidade)
    eleicao = Eleicao.query.filter_by(unidade=unidade).first_or_404()
    candidatos = Candidato.query.filter_by(unidade=unidade).order_by(Candidato.nome).all()
    total_eleitores = Funcionario.query.filter_by(unidade=unidade, ativo=True).count()
    dim = calcular_dimensionamento(total_eleitores)
    now = datetime.now().strftime('%d/%m/%Y às %H:%M')
    return render_template(
        'admin/relatorios/zeresima.html',
        unidade=unidade,
        eleicao=eleicao,
        candidatos=candidatos,
        total_eleitores=total_eleitores,
        total_candidatos=len(candidatos),
        dimensionamento=dim,
        now=now,
    )


@admin_bp.route('/eleicao/<unidade>/relatorio/boletim')
@login_required
def boletim_urna(unidade):
    _get_unidade_or_404(unidade)
    resultado = apurar_eleicao(unidade)
    now = datetime.now().strftime('%d/%m/%Y às %H:%M')
    return render_template(
        'admin/relatorios/boletim.html',
        resultado=resultado,
        unidade=unidade,
        now=now,
    )


@admin_bp.route('/eleicao/<unidade>/relatorio/eleitos')
@login_required
def lista_eleitos(unidade):
    _get_unidade_or_404(unidade)
    resultado = apurar_eleicao(unidade)
    now = datetime.now().strftime('%d/%m/%Y às %H:%M')
    eleitos = [c for c in resultado['candidatos'] if c['situacao'] in ('Titular', 'Suplente')]
    return render_template(
        'admin/relatorios/eleitos.html',
        resultado=resultado,
        eleitos=eleitos,
        unidade=unidade,
        now=now,
    )


@admin_bp.route('/eleicao/<unidade>/relatorio/classificacao')
@login_required
def classificacao_candidatos(unidade):
    _get_unidade_or_404(unidade)
    resultado = apurar_eleicao(unidade)
    now = datetime.now().strftime('%d/%m/%Y às %H:%M')
    return render_template(
        'admin/relatorios/classificacao.html',
        resultado=resultado,
        unidade=unidade,
        now=now,
    )


@admin_bp.route('/eleicao/<unidade>/relatorio/cartaz')
@login_required
def cartaz_eleitos(unidade):
    _get_unidade_or_404(unidade)
    resultado = apurar_eleicao(unidade)
    titulares = [c for c in resultado['candidatos'] if c['situacao'] == 'Titular']
    suplentes = [c for c in resultado['candidatos'] if c['situacao'] == 'Suplente']
    now = datetime.now().strftime('%d/%m/%Y às %H:%M')
    return render_template(
        'admin/relatorios/cartaz.html',
        resultado=resultado,
        titulares=titulares,
        suplentes=suplentes,
        unidade=unidade,
        now=now,
    )


@admin_bp.route('/eleicao/<unidade>/relatorio/votantes')
@login_required
def lista_votantes(unidade):
    _get_unidade_or_404(unidade)
    eleicao = Eleicao.query.filter_by(unidade=unidade).first_or_404()
    votantes = Funcionario.query.filter_by(unidade=unidade, votou=True).order_by(Funcionario.nome).all()

    # Enriquece cada votante com a data/hora do voto (via Voto.funcionario_id)
    votantes_data = []
    for f in votantes:
        voto = Voto.query.filter_by(funcionario_id=f.id).first()
        votantes_data.append({
            'funcionario': f,
            'data_hora_voto': voto.data_hora if voto else None,
        })

    now = datetime.now().strftime('%d/%m/%Y às %H:%M')
    return render_template(
        'admin/relatorios/votantes.html',
        votantes=votantes_data,
        unidade=unidade,
        eleicao=eleicao,
        total=len(votantes_data),
        now=now,
    )


@admin_bp.route('/eleicao/<unidade>/relatorio/nao-votantes')
@login_required
def lista_nao_votantes(unidade):
    _get_unidade_or_404(unidade)
    eleicao = Eleicao.query.filter_by(unidade=unidade).first_or_404()
    nao_votantes = (
        Funcionario.query
        .filter_by(unidade=unidade, votou=False, ativo=True)
        .order_by(Funcionario.nome)
        .all()
    )
    now = datetime.now().strftime('%d/%m/%Y às %H:%M')
    return render_template(
        'admin/relatorios/nao_votantes.html',
        nao_votantes=nao_votantes,
        unidade=unidade,
        eleicao=eleicao,
        total=len(nao_votantes),
        now=now,
    )


@admin_bp.route('/eleicao/<unidade>/relatorio/eleitores')
@login_required
def lista_eleitores(unidade):
    _get_unidade_or_404(unidade)
    eleicao = Eleicao.query.filter_by(unidade=unidade).first_or_404()
    eleitores = (
        Funcionario.query
        .filter_by(unidade=unidade, ativo=True)
        .order_by(Funcionario.nome)
        .all()
    )
    now = datetime.now().strftime('%d/%m/%Y às %H:%M')
    return render_template(
        'admin/relatorios/eleitores.html',
        eleitores=eleitores,
        unidade=unidade,
        eleicao=eleicao,
        total=len(eleitores),
        now=now,
    )


@admin_bp.route('/relatorio/participacao/dashboard')
@login_required
def participacao_dashboard():
    dados = calcular_participacao_geral()
    now = datetime.now().strftime('%d/%m/%Y às %H:%M')
    return render_template(
        'admin/relatorios/participacao_dashboard.html',
        dados=dados,
        now=now,
    )


@admin_bp.route('/relatorio/participacao/nominal')
@login_required
def participacao_nominal():
    unidade_filtro = request.args.get('unidade', '').strip()
    if unidade_filtro and unidade_filtro not in UNIDADES:
        abort(404)

    unidades_alvo = [unidade_filtro] if unidade_filtro else UNIDADES
    dados_nominais = []
    for unidade in unidades_alvo:
        funcionarios = (
            Funcionario.query
            .filter_by(unidade=unidade, ativo=True)
            .order_by(Funcionario.nome)
            .all()
        )
        votaram = sum(1 for f in funcionarios if f.votou)
        dados_nominais.append({
            'unidade': unidade,
            'funcionarios': funcionarios,
            'total': len(funcionarios),
            'votaram': votaram,
            'pendentes': len(funcionarios) - votaram,
        })

    now = datetime.now().strftime('%d/%m/%Y às %H:%M')
    return render_template(
        'admin/relatorios/participacao_nominal.html',
        dados_nominais=dados_nominais,
        unidade_filtro=unidade_filtro,
        unidades=UNIDADES,
        now=now,
    )
