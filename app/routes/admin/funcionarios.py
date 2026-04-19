from flask import render_template, request, redirect, url_for, flash
from . import admin_bp
from ...extensions import db
from ...models import Funcionario
from ...constants import UNIDADES
from ...utils import login_required


@admin_bp.route('/funcionarios')
@login_required
def funcionarios():
    return render_template('admin/funcionarios.html',
                           funcionarios=Funcionario.query.order_by(Funcionario.unidade, Funcionario.nome).all(),
                           unidades=UNIDADES)


@admin_bp.route('/funcionarios/adicionar', methods=['POST'])
@login_required
def adicionar_funcionario():
    matricula = request.form['matricula'].strip()
    nome = request.form['nome'].strip()
    unidade = request.form['unidade'].strip()
    if matricula and nome and unidade:
        if Funcionario.query.filter_by(matricula=matricula).first():
            flash('Matrícula já cadastrada.', 'danger')
        else:
            db.session.add(Funcionario(matricula=matricula, nome=nome, unidade=unidade))
            db.session.commit()
            flash(f'Funcionário adicionado em {unidade}!', 'success')
    return redirect(url_for('admin.funcionarios'))


@admin_bp.route('/funcionarios/remover/<int:id>')
@login_required
def remover_funcionario(id):
    funcionario = Funcionario.query.get_or_404(id)
    db.session.delete(funcionario)
    db.session.commit()
    flash('Funcionário removido.', 'warning')
    return redirect(url_for('admin.funcionarios'))
