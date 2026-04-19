from flask import render_template, request, redirect, url_for, flash
from . import admin_bp
from ...extensions import db
from ...models import Candidato
from ...constants import UNIDADES
from ...services.foto import allowed_file, salvar_foto, deletar_foto, migrar_base64
from ...utils import login_required


@admin_bp.route('/candidatos')
@login_required
def candidatos():
    return render_template('admin/candidatos.html',
                           candidatos=Candidato.query.order_by(Candidato.unidade, Candidato.nome).all(),
                           unidades=UNIDADES)


@admin_bp.route('/candidatos/adicionar', methods=['POST'])
@login_required
def adicionar_candidato():
    nome = request.form['nome'].strip()
    unidade = request.form['unidade'].strip()
    if nome and unidade:
        candidato = Candidato(nome=nome, cargo='', unidade=unidade)
        db.session.add(candidato)
        db.session.flush()
        file = request.files.get('foto')
        if file and file.filename and allowed_file(file.filename):
            candidato.foto = salvar_foto(file)
        db.session.commit()
        flash(f'Candidato adicionado em {unidade}!', 'success')
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
    deletar_foto(candidato.foto)
    db.session.delete(candidato)
    db.session.commit()
    flash('Candidato removido.', 'warning')
    return redirect(url_for('admin.candidatos'))


@admin_bp.route('/migrar-fotos', methods=['POST'])
@login_required
def migrar_fotos():
    count = sum(1 for c in Candidato.query.all() if migrar_base64(c))
    db.session.commit()
    flash(f'{count} foto(s) migrada(s) para arquivos com sucesso.', 'success')
    return redirect(url_for('admin.candidatos'))
