from flask import render_template, request, redirect, url_for, flash
from . import admin_bp
from ...extensions import db
from ...models import Candidato, Funcionario, HistoricoEleicao
from ...constants import UNIDADES
from ...services.foto import allowed_file, salvar_foto, deletar_foto, migrar_base64
from ...utils import login_required


@admin_bp.route('/candidatos')
@login_required
def candidatos():
    search = request.args.get('search', '').strip()
    unidade_filtro = request.args.get('unidade', '')
    page = request.args.get('page', 1, type=int)

    query = Candidato.query
    if search:
        query = query.filter(Candidato.nome.ilike(f'%{search}%'))
    if unidade_filtro:
        query = query.filter_by(unidade=unidade_filtro)

    pagination = query.order_by(Candidato.unidade, Candidato.nome).paginate(
        page=page, per_page=20, error_out=False
    )

    # Funcionários disponíveis por unidade para vinculação no formulário
    funcionarios_por_unidade = {
        u: Funcionario.query.filter_by(unidade=u, ativo=True).order_by(Funcionario.nome).all()
        for u in UNIDADES
    }

    return render_template(
        'admin/candidatos.html',
        candidatos=pagination.items,
        pagination=pagination,
        unidades=UNIDADES,
        search=search,
        unidade_filtro=unidade_filtro,
        total_geral=Candidato.query.count(),
        funcionarios_por_unidade=funcionarios_por_unidade,
    )


@admin_bp.route('/candidatos/adicionar', methods=['POST'])
@login_required
def adicionar_candidato():
    nome = request.form['nome'].strip()
    unidade = request.form['unidade'].strip()
    funcionario_id = request.form.get('funcionario_id') or None
    if funcionario_id:
        funcionario_id = int(funcionario_id)
    if nome and unidade:
        candidato = Candidato(nome=nome, cargo='', unidade=unidade, funcionario_id=funcionario_id)
        db.session.add(candidato)
        db.session.flush()
        file = request.files.get('foto')
        if file and file.filename and allowed_file(file.filename):
            candidato.foto = salvar_foto(file)
        db.session.commit()
        flash(f'Candidato adicionado em {unidade}!', 'success')
    return redirect(url_for('admin.candidatos'))


@admin_bp.route('/candidatos/editar/<int:id>', methods=['POST'])
@login_required
def editar_candidato(id):
    candidato = Candidato.query.get_or_404(id)
    candidato.nome = request.form.get('nome', '').strip() or candidato.nome
    candidato.unidade = request.form.get('unidade', '').strip() or candidato.unidade
    funcionario_id = request.form.get('funcionario_id') or None
    candidato.funcionario_id = int(funcionario_id) if funcionario_id else None
    db.session.commit()
    flash('Candidato atualizado!', 'success')
    return redirect(url_for('admin.candidatos'))


@admin_bp.route('/candidatos/foto/<int:id>', methods=['POST'])
@login_required
def upload_foto(id):
    candidato = Candidato.query.get_or_404(id)
    file = request.files.get('foto')
    if not file or not file.filename:
        flash('Nenhum arquivo selecionado.', 'danger')
        return redirect(url_for('admin.candidatos'))
    if not allowed_file(file.filename):
        flash('Formato inválido. Use JPG, PNG ou GIF.', 'danger')
        return redirect(url_for('admin.candidatos'))
    deletar_foto(candidato.foto)
    candidato.foto = salvar_foto(file)
    db.session.commit()
    flash('Foto atualizada com sucesso!', 'success')
    return redirect(url_for('admin.candidatos'))


@admin_bp.route('/candidatos/remover/<int:id>')
@login_required
def remover_candidato(id):
    candidato = Candidato.query.get_or_404(id)
    foto = candidato.foto
    db.session.delete(candidato)
    db.session.commit()
    foto_em_historico = foto and HistoricoEleicao.query.filter(
        HistoricoEleicao.dados.like(f'%{foto}%')
    ).first()
    if not foto_em_historico:
        deletar_foto(foto)
    flash('Candidato removido.', 'warning')
    return redirect(url_for('admin.candidatos'))


@admin_bp.route('/migrar-fotos', methods=['POST'])
@login_required
def migrar_fotos():
    count = sum(1 for c in Candidato.query.all() if migrar_base64(c))
    db.session.commit()
    flash(f'{count} foto(s) migrada(s) para arquivos com sucesso.', 'success')
    return redirect(url_for('admin.candidatos'))
