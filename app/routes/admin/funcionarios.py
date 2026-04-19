from flask import render_template, request, redirect, url_for, flash
from . import admin_bp
from ...extensions import db
from ...models import Funcionario
from ...constants import UNIDADES
from ...utils import login_required


@admin_bp.route('/funcionarios')
@login_required
def funcionarios():
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '')
    unidade_filtro = request.args.get('unidade', '')
    page = request.args.get('page', 1, type=int)

    query = Funcionario.query
    if search:
        query = query.filter(
            db.or_(
                Funcionario.nome.ilike(f'%{search}%'),
                Funcionario.matricula.ilike(f'%{search}%'),
            )
        )
    if status == 'votou':
        query = query.filter_by(votou=True)
    elif status == 'pendente':
        query = query.filter_by(votou=False)
    if unidade_filtro:
        query = query.filter_by(unidade=unidade_filtro)

    pagination = query.order_by(Funcionario.unidade, Funcionario.nome).paginate(
        page=page, per_page=25, error_out=False
    )
    return render_template(
        'admin/funcionarios.html',
        funcionarios=pagination.items,
        pagination=pagination,
        unidades=UNIDADES,
        search=search,
        status=status,
        unidade_filtro=unidade_filtro,
        total_geral=Funcionario.query.count(),
        total_votou=Funcionario.query.filter_by(votou=True).count(),
        total_pendente=Funcionario.query.filter_by(votou=False).count(),
    )


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
