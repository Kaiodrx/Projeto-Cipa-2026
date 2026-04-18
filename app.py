import os
import base64
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
    votos = db.relationship('Voto', backref='candidato', lazy=True)


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
    status = db.Column(db.String(20), default='fechada')


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
        db.session.add(Eleicao(status='fechada'))
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
    eleicao = Eleicao.query.first()
    return render_template('admin/dashboard.html',
                           total_candidatos=Candidato.query.count(),
                           total_funcionarios=Funcionario.query.count(),
                           total_votos=Voto.query.count(),
                           eleicao=eleicao,
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
    cargo = request.form['cargo'].strip()
    unidade = request.form['unidade'].strip()
    if nome and cargo and unidade:
        candidato = Candidato(nome=nome, cargo=cargo, unidade=unidade)
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
    eleicao = Eleicao.query.first()
    candidatos_por_unidade = {
        u: Candidato.query.filter_by(unidade=u).all() for u in UNIDADES
    }
    funcionarios_por_unidade = {
        u: Funcionario.query.filter_by(unidade=u).count() for u in UNIDADES
    }
    return render_template('admin/eleicao.html',
                           eleicao=eleicao,
                           candidatos_por_unidade=candidatos_por_unidade,
                           funcionarios_por_unidade=funcionarios_por_unidade,
                           unidades=UNIDADES)


@app.route('/admin/eleicao/abrir')
@login_required
def abrir_eleicao():
    eleicao = Eleicao.query.first()
    eleicao.status = 'aberta'
    db.session.commit()
    flash('Eleição aberta com sucesso!', 'success')
    return redirect(url_for('gerenciar_eleicao'))


@app.route('/admin/eleicao/fechar')
@login_required
def fechar_eleicao():
    eleicao = Eleicao.query.first()
    eleicao.status = 'fechada'
    db.session.commit()
    flash('Eleição encerrada.', 'warning')
    return redirect(url_for('gerenciar_eleicao'))


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


# ── Votação pública ────────────────────────────────────────────────────────────

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/votacao', methods=['GET', 'POST'])
def login_votacao():
    eleicao = Eleicao.query.first()
    if request.method == 'POST':
        matricula = request.form['matricula'].strip()
        unidade = request.form['unidade'].strip()
        funcionario = Funcionario.query.filter_by(matricula=matricula).first()
        if not funcionario:
            flash('Matrícula não encontrada.', 'danger')
        elif funcionario.unidade != unidade:
            flash('Unidade incorreta para esta matrícula.', 'danger')
        elif funcionario.votou:
            flash('Você já votou nesta eleição.', 'warning')
        elif eleicao.status != 'aberta':
            flash('A eleição não está aberta no momento.', 'warning')
        else:
            session['funcionario_id'] = funcionario.id
            return redirect(url_for('votar'))
    return render_template('votacao/login.html', eleicao=eleicao, unidades=UNIDADES)


@app.route('/votar', methods=['GET', 'POST'])
def votar():
    if 'funcionario_id' not in session:
        return redirect(url_for('login_votacao'))
    eleicao = Eleicao.query.first()
    if eleicao.status != 'aberta':
        flash('A eleição não está aberta.', 'warning')
        return redirect(url_for('login_votacao'))
    funcionario = Funcionario.query.get(session['funcionario_id'])
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
