from flask import render_template, request, redirect, url_for, session, flash
from . import public_bp
from ...extensions import db
from ...models import Funcionario, Candidato, Eleicao, Voto
from ...constants import UNIDADES


@public_bp.route('/')
def home():
    return render_template('home.html')


@public_bp.route('/votacao', methods=['GET', 'POST'])
def login_votacao():
    if request.method == 'POST':
        matricula = request.form['matricula'].strip()
        unidade = request.form['unidade'].strip()
        funcionario = Funcionario.query.filter_by(matricula=matricula).first()
        eleicao = Eleicao.query.filter_by(unidade=unidade).first()
        if not funcionario:
            flash('Matrícula não encontrada.', 'danger')
        elif funcionario.unidade != unidade:
            flash('Unidade incorreta para esta matrícula.', 'danger')
        elif funcionario.votou:
            flash('Você já votou nesta eleição.', 'warning')
        elif not eleicao or eleicao.status != 'aberta':
            flash('A eleição desta unidade não está aberta no momento.', 'warning')
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
            db.session.add(Voto(candidato_id=int(candidato_id)))
            funcionario.votou = True
            db.session.commit()
            session.pop('funcionario_id', None)
            return redirect(url_for('public.confirmacao'))
    candidatos = Candidato.query.filter_by(unidade=funcionario.unidade).all()
    return render_template('votacao/votar.html', candidatos=candidatos, funcionario=funcionario)


@public_bp.route('/confirmacao')
def confirmacao():
    return render_template('votacao/confirmacao.html')
