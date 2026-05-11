import json
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash
from . import admin_bp
from ...extensions import db
from ...models import Candidato, Funcionario, Voto, Eleicao, HistoricoEleicao
from ...constants import UNIDADES
from ...utils import login_required
from ...services.dimensionamento import calcular_dimensionamento


@admin_bp.route('/resultado')
@login_required
def resultado():
    resultado_por_unidade = {}
    for unidade in UNIDADES:
        candidatos_u = Candidato.query.filter_by(unidade=unidade).all()
        dados = sorted([(c, len(c.votos)) for c in candidatos_u], key=lambda x: x[1], reverse=True)
        total = sum(v for _, v in dados)
        votos_unidade = Funcionario.query.filter_by(unidade=unidade, votou=True).count()
        total_func = Funcionario.query.filter_by(unidade=unidade).count()
        resultado_por_unidade[unidade] = {
            'dados': dados,
            'total_votos': total,
            'votaram': votos_unidade,
            'total_funcionarios': total_func,
        }
    now = datetime.now().strftime('%d/%m/%Y às %H:%M')
    return render_template('admin/resultado.html',
                           resultado_por_unidade=resultado_por_unidade,
                           total_votos_geral=Voto.query.count(),
                           unidades=UNIDADES,
                           now=now)


@admin_bp.route('/resultado/finalizar', methods=['POST'])
@login_required
def finalizar_eleicao():
    titulo = request.form.get('titulo', '').strip() or f'Eleição CIPA 2026 — {datetime.now().strftime("%d/%m/%Y")}'
    unidades_dados = []
    total_geral = 0

    for unidade in UNIDADES:
        candidatos_u = Candidato.query.filter_by(unidade=unidade).all()
        total_eleitores = Funcionario.query.filter_by(unidade=unidade, ativo=True).count()
        dim = calcular_dimensionamento(total_eleitores)
        n_t = dim['titulares']
        n_s = dim['suplentes']

        dados_u = sorted(
            [(c.nome, c.foto, len(c.votos)) for c in candidatos_u],
            key=lambda x: x[2],
            reverse=True,
        )
        total_u = sum(v for _, _, v in dados_u)
        total_geral += total_u

        candidatos_snap = []
        for i, (nome, foto, votos) in enumerate(dados_u):
            pos = i + 1
            if pos <= n_t:
                situacao = 'Titular'
            elif pos <= n_t + n_s:
                situacao = 'Suplente'
            else:
                situacao = 'Não eleito'
            candidatos_snap.append({
                'nome': nome,
                'foto': foto,
                'votos': votos,
                'pct': round(votos / total_u * 100, 1) if total_u > 0 else 0,
                'situacao': situacao,
            })

        unidades_dados.append({
            'unidade': unidade,
            'total_votos': total_u,
            'votaram': Funcionario.query.filter_by(unidade=unidade, votou=True).count(),
            'total_funcionarios': total_eleitores,
            'dimensionamento': dim,
            'candidatos': candidatos_snap,
        })

    snapshot = {
        'titulo': titulo,
        'data': datetime.now().strftime('%d/%m/%Y às %H:%M'),
        'total_geral': total_geral,
        'unidades': unidades_dados,
    }
    db.session.add(HistoricoEleicao(titulo=titulo, dados=json.dumps(snapshot)))
    Voto.query.delete()
    Funcionario.query.update({'votou': False})
    for e in Eleicao.query.all():
        e.status = 'fechada'
    db.session.commit()
    flash('Eleição finalizada e salva no histórico com sucesso!', 'success')
    return redirect(url_for('admin.historico'))
