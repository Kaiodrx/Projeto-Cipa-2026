import io
from flask import render_template, request, redirect, url_for, flash, send_file
from openpyxl import load_workbook, Workbook
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


@admin_bp.route('/funcionarios/modelo')
@login_required
def modelo_funcionarios():
    wb = Workbook()
    ws = wb.active
    ws.title = 'Funcionarios'
    ws.append(['matricula', 'nome', 'unidade'])
    ws.append(['00001', 'João da Silva', 'Unidade A'])
    ws.append(['00002', 'Maria Oliveira', 'Unidade B'])

    col_widths = {'A': 14, 'B': 40, 'C': 30}
    for col, width in col_widths.items():
        ws.column_dimensions[col].width = width

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(
        buf,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='modelo_funcionarios.xlsx',
    )


@admin_bp.route('/funcionarios/importar', methods=['POST'])
@login_required
def importar_funcionarios():
    arquivo = request.files.get('planilha')
    if not arquivo or not arquivo.filename.endswith('.xlsx'):
        flash('Envie um arquivo Excel (.xlsx) válido.', 'danger')
        return redirect(url_for('admin.funcionarios'))

    try:
        wb = load_workbook(arquivo, read_only=True, data_only=True)
        ws = wb.active

        # Carrega todos os funcionários existentes de uma vez (1 consulta, qualquer tamanho)
        existentes = {f.matricula: f for f in Funcionario.query.all()}
        unidades_validas = set(UNIDADES)
        adicionados = atualizados = erros = 0

        for row in ws.iter_rows(min_row=2, values_only=True):
            if not any(row):
                continue
            if len(row) < 3:
                erros += 1
                continue

            matricula = str(row[0]).strip() if row[0] is not None else ''
            nome = str(row[1]).strip() if row[1] is not None else ''
            unidade = str(row[2]).strip() if row[2] is not None else ''

            if not matricula or not nome or not unidade:
                erros += 1
                continue

            if unidade not in unidades_validas:
                erros += 1
                continue

            if matricula in existentes:
                existentes[matricula].nome = nome
                existentes[matricula].unidade = unidade
                atualizados += 1
            else:
                novo = Funcionario(matricula=matricula, nome=nome, unidade=unidade)
                db.session.add(novo)
                existentes[matricula] = novo  # evita duplicatas dentro da mesma planilha
                adicionados += 1

        db.session.commit()
        wb.close()

        partes = []
        if adicionados:
            partes.append(f'{adicionados} adicionado(s)')
        if atualizados:
            partes.append(f'{atualizados} atualizado(s)')
        if erros:
            partes.append(f'{erros} linha(s) ignorada(s) por dado inválido')

        flash('Importação concluída: ' + ', '.join(partes) + '.', 'success' if not erros or adicionados or atualizados else 'warning')

    except Exception:
        db.session.rollback()
        flash('Erro ao processar a planilha. Verifique se o arquivo está no formato correto.', 'danger')

    return redirect(url_for('admin.funcionarios'))


@admin_bp.route('/funcionarios/remover/<int:id>')
@login_required
def remover_funcionario(id):
    funcionario = Funcionario.query.get_or_404(id)
    db.session.delete(funcionario)
    db.session.commit()
    flash('Funcionário removido.', 'warning')
    return redirect(url_for('admin.funcionarios'))
