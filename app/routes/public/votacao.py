from flask import render_template, request, redirect, url_for, session, flash
from . import public_bp
from ...extensions import db
from ...models import Funcionario, Candidato, Eleicao, Voto
from ...constants import UNIDADES
from ...services.eleitor import validar_eleitor


@public_bp.route('/')
def home():
    return render_template('home.html')


@public_bp.route('/votacao', methods=['GET', 'POST'])
def login_votacao():
    if request.method == 'POST':
        matricula = request.form.get('matricula', '').strip()
        unidade = request.form.get('unidade', '').strip()
        data_nascimento = request.form.get('data_nascimento', '').strip()

        funcionario, erro = validar_eleitor(matricula, unidade, data_nascimento)
        if erro:
            categoria = 'warning' if 'já votou' in erro or 'não está aberta' in erro else 'danger'
            flash(erro, categoria)
        else:
            session['funcionario_id'] = funcionario.id
            return redirect(url_for('public.votar'))
    return render_template('votacao/login.html', unidades=UNIDADES)


@public_bp.route('/votar', methods=['GET', 'POST'])
def votar():
    if 'funcionario_id' not in session:
        return redirect(url_for('public.login_votacao'))
    funcionario = Funcionario.query.get(session['funcionario_id'])
    eleicao = Eleicao.query.filter_by(unidade=funcionario.unidade).first()
    if not eleicao or eleicao.status != 'aberta':
        flash('A eleição desta unidade não está aberta.', 'warning')
        return redirect(url_for('public.login_votacao'))
    if funcionario.votou:
        session.pop('funcionario_id', None)
        flash('Você já votou.', 'warning')
        return redirect(url_for('public.login_votacao'))
    if request.method == 'POST':
        candidato_id = request.form.get('candidato_id')
        if candidato_id:
            db.session.add(Voto(candidato_id=int(candidato_id), funcionario_id=funcionario.id))
            funcionario.votou = True
            db.session.commit()
            session.pop('funcionario_id', None)
            return redirect(url_for('public.confirmacao'))
    candidatos = Candidato.query.filter_by(unidade=funcionario.unidade).all()
    return render_template('votacao/votar.html', candidatos=candidatos, funcionario=funcionario)


@public_bp.route('/confirmacao')
def confirmacao():
    return render_template('votacao/confirmacao.html')
