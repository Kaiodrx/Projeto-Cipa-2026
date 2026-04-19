import os
import base64
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'cipa2026_chave_secreta')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///cipa.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

UNIDADES = [
    'UTD SOBRADINHO',
    'UTD PLANALTINA',
    'UTD SIA',
    'SEDE PARK SHOPPING',
    'UTD TAGUATINGA',
    'UTD LAGO SUL',
    'UTD SÃO SEBASTIÃO',
]

db = SQLAlchemy(app)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ── Modelos ────────────────────────────────────────────────────────────────────

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Candidato(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cargo = db.Column(db.String(100), nullable=False)
    unidade = db.Column(db.String(50), nullable=True)
    foto = db.Column(db.Text, nullable=True)
    votos = db.relationship('Voto', backref='candidato', lazy=True, cascade='all, delete-orphan')


class Funcionario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    matricula = db.Column(db.String(20), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    unidade = db.Column(db.String(50), nullable=True)
    votou = db.Column(db.Boolean, default=False)


class Voto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    candidato_id = db.Column(db.Integer, db.ForeignKey('candidato.id'), nullable=False)


class Eleicao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unidade = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), default='fechada')


class HistoricoEleicao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    data = db.Column(db.DateTime, default=datetime.utcnow)
    dados = db.Column(db.Text, nullable=False)  # JSON com resultado completo


# ── Proteção de rotas admin ────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('login_admin'))
        return f(*args, **kwargs)
    return decorated


# ── Inicialização do banco ─────────────────────────────────────────────────────

def init_db():
    db.create_all()
    with db.engine.connect() as conn:
        for sql in [
            "ALTER TABLE candidato ADD COLUMN foto TEXT",
            "ALTER TABLE candidato ADD COLUMN unidade VARCHAR(50)",
            "ALTER TABLE funcionario ADD COLUMN unidade VARCHAR(50)",
            "ALTER TABLE eleicao ADD COLUMN unidade VARCHAR(50)",
        ]:
            try:
                conn.execute(db.text(sql))
                conn.commit()
            except Exception:
                pass
    if not Admin.query.first():
        db.session.add(Admin(
            username='admin',
            password=generate_password_hash('cipa2026')
        ))
        db.session.commit()
    for unidade in UNIDADES:
        if not Eleicao.query.filter_by(unidade=unidade).first():
            db.session.add(Eleicao(unidade=unidade, status='fechada'))
    db.session.commit()


# ── Autenticação admin ─────────────────────────────────────────────────────────

@app.route('/admin/login', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            session['admin_id'] = admin.id
            return redirect(url_for('dashboard'))
        flash('Usuário ou senha incorretos.', 'danger')
    return render_template('login_admin.html')


@app.route('/admin/logout')
def logout_admin():
    session.pop('admin_id', None)
    return redirect(url_for('login_admin'))


# ── Painel admin ───────────────────────────────────────────────────────────────

@app.route('/admin')
@login_required
def dashboard():
    eleicoes = {e.unidade: e for e in Eleicao.query.all()}
    abertas = sum(1 for e in eleicoes.values() if e.status == 'aberta')
    andamento = []
    for unidade in UNIDADES:
        eleicao = eleicoes.get(unidade)
        if not eleicao or eleicao.status != 'aberta':
            continue
        total_func = Funcionario.query.filter_by(unidade=unidade).count()
        votaram = Funcionario.query.filter_by(unidade=unidade, votou=True).count()
        votos = Voto.query.join(Candidato).filter(Candidato.unidade == unidade).count()
        pct = round(votaram / total_func * 100, 1) if total_func > 0 else 0
        andamento.append({
            'unidade': unidade,
            'votaram': votaram,
            'total': total_func,
            'votos': votos,
            'pct': pct,
        })
    return render_template('admin/dashboard.html',
                           total_candidatos=Candidato.query.count(),
                           total_funcionarios=Funcionario.query.count(),
                           total_votos=Voto.query.count(),
                           unidades_abertas=abertas,
                           total_unidades=len(UNIDADES),
                           andamento=andamento,
                           unidades=UNIDADES)


# ── Candidatos ─────────────────────────────────────────────────────────────────

@app.route('/admin/candidatos')
@login_required
def candidatos():
    return render_template('admin/candidatos.html',
                           candidatos=Candidato.query.order_by(Candidato.unidade, Candidato.nome).all(),
                           unidades=UNIDADES)


@app.route('/admin/candidatos/adicionar', methods=['POST'])
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
            candidato.foto = _foto_para_base64(file)
        db.session.commit()
        flash(f'Candidato adicionado em {unidade}!', 'success')
    return redirect(url_for('candidatos'))


@app.route('/admin/candidatos/foto/<int:id>', methods=['POST'])
@login_required
def upload_foto(id):
    candidato = Candidato.query.get_or_404(id)
    file = request.files.get('foto')
    if not file or not file.filename:
        flash('Nenhum arquivo selecionado.', 'danger')
        return redirect(url_for('candidatos'))
    if not allowed_file(file.filename):
        flash('Formato inválido. Use JPG ou PNG.', 'danger')
        return redirect(url_for('candidatos'))
    candidato.foto = _foto_para_base64(file)
    db.session.commit()
    flash('Foto atualizada com sucesso!', 'success')
    return redirect(url_for('candidatos'))


def _foto_para_base64(file):
    ext = file.filename.rsplit('.', 1)[1].lower()
    mime = 'image/jpeg' if ext in ('jpg', 'jpeg') else f'image/{ext}'
    data = base64.b64encode(file.read()).decode('utf-8')
    return f'data:{mime};base64,{data}'


@app.route('/admin/candidatos/remover/<int:id>')
@login_required
def remover_candidato(id):
    candidato = Candidato.query.get_or_404(id)
    db.session.delete(candidato)
    db.session.commit()
    flash('Candidato removido.', 'warning')
    return redirect(url_for('candidatos'))


# ── Funcionários ───────────────────────────────────────────────────────────────

@app.route('/admin/funcionarios')
@login_required
def funcionarios():
    return render_template('admin/funcionarios.html',
                           funcionarios=Funcionario.query.order_by(Funcionario.unidade, Funcionario.nome).all(),
                           unidades=UNIDADES)


@app.route('/admin/funcionarios/adicionar', methods=['POST'])
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
    return redirect(url_for('funcionarios'))


@app.route('/admin/funcionarios/remover/<int:id>')
@login_required
def remover_funcionario(id):
    funcionario = Funcionario.query.get_or_404(id)
    db.session.delete(funcionario)
    db.session.commit()
    flash('Funcionário removido.', 'warning')
    return redirect(url_for('funcionarios'))


# ── Eleição ────────────────────────────────────────────────────────────────────

@app.route('/admin/eleicao')
@login_required
def gerenciar_eleicao():
    eleicoes = {e.unidade: e for e in Eleicao.query.all()}
    candidatos_por_unidade = {u: Candidato.query.filter_by(unidade=u).all() for u in UNIDADES}
    funcionarios_por_unidade = {u: Funcionario.query.filter_by(unidade=u).count() for u in UNIDADES}
    return render_template('admin/eleicao.html',
                           eleicoes=eleicoes,
                           candidatos_por_unidade=candidatos_por_unidade,
                           funcionarios_por_unidade=funcionarios_por_unidade,
                           unidades=UNIDADES)


@app.route('/admin/eleicao/abrir-todas')
@login_required
def abrir_todas():
    for e in Eleicao.query.all():
        e.status = 'aberta'
    db.session.commit()
    flash('Todas as unidades foram abertas!', 'success')
    return redirect(url_for('gerenciar_eleicao'))


@app.route('/admin/eleicao/fechar-todas')
@login_required
def fechar_todas():
    for e in Eleicao.query.all():
        e.status = 'fechada'
    db.session.commit()
    flash('Todas as unidades foram encerradas.', 'warning')
    return redirect(url_for('gerenciar_eleicao'))


@app.route('/admin/eleicao/<unidade>/abrir')
@login_required
def abrir_eleicao(unidade):
    eleicao = Eleicao.query.filter_by(unidade=unidade).first_or_404()
    eleicao.status = 'aberta'
    db.session.commit()
    flash(f'{unidade} — eleição aberta!', 'success')
    return redirect(url_for('gerenciar_eleicao'))


@app.route('/admin/eleicao/<unidade>/fechar')
@login_required
def fechar_eleicao(unidade):
    eleicao = Eleicao.query.filter_by(unidade=unidade).first_or_404()
    eleicao.status = 'fechada'
    db.session.commit()
    flash(f'{unidade} — eleição encerrada.', 'warning')
    return redirect(url_for('gerenciar_eleicao'))


# ── Participação ───────────────────────────────────────────────────────────────

@app.route('/admin/participacao')
@login_required
def participacao():
    dados_por_unidade = {}
    total_votaram = 0
    total_funcionarios = 0
    for unidade in UNIDADES:
        todos = Funcionario.query.filter_by(unidade=unidade).all()
        votaram = [f for f in todos if f.votou]
        pendentes = [f for f in todos if not f.votou]
        dados_por_unidade[unidade] = {
            'total': len(todos),
            'votaram': votaram,
            'pendentes': pendentes,
        }
        total_votaram += len(votaram)
        total_funcionarios += len(todos)
    now = datetime.now().strftime('%d/%m/%Y às %H:%M')
    return render_template('admin/participacao.html',
                           dados_por_unidade=dados_por_unidade,
                           total_funcionarios=total_funcionarios,
                           total_votaram=total_votaram,
                           total_pendentes=total_funcionarios - total_votaram,
                           unidades=UNIDADES,
                           now=now)


# ── Resultado ──────────────────────────────────────────────────────────────────

@app.route('/admin/resultado')
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
    total_votos_geral = Voto.query.count()
    return render_template('admin/resultado.html',
                           resultado_por_unidade=resultado_por_unidade,
                           total_votos_geral=total_votos_geral,
                           unidades=UNIDADES,
                           now=now)


# ── Finalizar eleição e histórico ─────────────────────────────────────────────

@app.route('/admin/resultado/finalizar', methods=['POST'])
@login_required
def finalizar_eleicao():
    titulo = request.form.get('titulo', '').strip() or f'Eleição CIPA 2026 — {datetime.now().strftime("%d/%m/%Y")}'
    unidades_dados = []
    total_geral = 0
    for unidade in UNIDADES:
        candidatos_u = Candidato.query.filter_by(unidade=unidade).all()
        dados_u = sorted([(c.nome, c.foto, len(c.votos)) for c in candidatos_u], key=lambda x: x[2], reverse=True)
        total_u = sum(v for _, _, v in dados_u)
        total_geral += total_u
        unidades_dados.append({
            'unidade': unidade,
            'total_votos': total_u,
            'votaram': Funcionario.query.filter_by(unidade=unidade, votou=True).count(),
            'total_funcionarios': Funcionario.query.filter_by(unidade=unidade).count(),
            'candidatos': [
                {
                    'nome': nome,
                    'foto': foto,
                    'votos': votos,
                    'pct': round(votos / total_u * 100, 1) if total_u > 0 else 0,
                }
                for nome, foto, votos in dados_u
            ],
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
    return redirect(url_for('historico'))


@app.route('/admin/historico')
@login_required
def historico():
    registros = HistoricoEleicao.query.order_by(HistoricoEleicao.data.desc()).all()
    return render_template('admin/historico.html', registros=registros)


@app.route('/admin/historico/<int:id>')
@login_required
def ver_historico(id):
    registro = HistoricoEleicao.query.get_or_404(id)
    snapshot = json.loads(registro.dados)
    return render_template('admin/historico_detalhe.html', registro=registro, snapshot=snapshot)


@app.route('/admin/historico/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_historico(id):
    registro = HistoricoEleicao.query.get_or_404(id)
    db.session.delete(registro)
    db.session.commit()
    flash('Registro removido do histórico.', 'warning')
    return redirect(url_for('historico'))


# ── Votação pública ────────────────────────────────────────────────────────────

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/votacao', methods=['GET', 'POST'])
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
            return redirect(url_for('votar'))
    return render_template('votacao/login.html', unidades=UNIDADES)


@app.route('/votar', methods=['GET', 'POST'])
def votar():
    if 'funcionario_id' not in session:
        return redirect(url_for('login_votacao'))
    funcionario = Funcionario.query.get(session['funcionario_id'])
    eleicao = Eleicao.query.filter_by(unidade=funcionario.unidade).first()
    if not eleicao or eleicao.status != 'aberta':
        flash('A eleição desta unidade não está aberta.', 'warning')
        return redirect(url_for('login_votacao'))
    if funcionario.votou:
        session.pop('funcionario_id', None)
        flash('Você já votou.', 'warning')
        return redirect(url_for('login_votacao'))
    if request.method == 'POST':
        candidato_id = request.form.get('candidato_id')
        if candidato_id:
            db.session.add(Voto(candidato_id=int(candidato_id)))
            funcionario.votou = True
            db.session.commit()
            session.pop('funcionario_id', None)
            return redirect(url_for('confirmacao'))
    candidatos = Candidato.query.filter_by(unidade=funcionario.unidade).all()
    return render_template('votacao/votar.html',
                           candidatos=candidatos,
                           funcionario=funcionario)


@app.route('/confirmacao')
def confirmacao():
    return render_template('votacao/confirmacao.html')


with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=True)
