import os
from flask import Flask
from werkzeug.security import generate_password_hash
from .extensions import db
from config import Config


def create_app(config_class=Config):
    basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    app = Flask(
        __name__,
        template_folder=os.path.join(basedir, 'templates'),
        static_folder=os.path.join(basedir, 'static'),
        instance_path=os.path.join(basedir, 'instance'),
    )
    app.config.from_object(config_class)
    app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)

    from .routes.admin import admin_bp
    from .routes.public import public_bp
    app.register_blueprint(admin_bp)
    app.register_blueprint(public_bp)

    if not app.config.get('TESTING'):
        with app.app_context():
            _init_db()

    return app


def _init_db():
    from .models import Admin, Eleicao
    from .constants import UNIDADES

    db.create_all()

    # Migração incremental: adiciona colunas novas sem destruir dados existentes.
    # Cada ALTER TABLE está em try/except pois falha silenciosamente se a coluna já existe.
    _alter_stmts = [
        # Candidato
        "ALTER TABLE candidato ADD COLUMN foto TEXT",
        "ALTER TABLE candidato ADD COLUMN unidade VARCHAR(50)",
        "ALTER TABLE candidato ADD COLUMN funcionario_id INTEGER REFERENCES funcionario(id)",
        # Funcionario
        "ALTER TABLE funcionario ADD COLUMN unidade VARCHAR(50)",
        "ALTER TABLE funcionario ADD COLUMN ativo BOOLEAN DEFAULT 1",
        "ALTER TABLE funcionario ADD COLUMN data_admissao DATE",
        "ALTER TABLE funcionario ADD COLUMN data_nascimento DATE",
        "ALTER TABLE funcionario ADD COLUMN setor VARCHAR(100)",
        "ALTER TABLE funcionario ADD COLUMN cargo VARCHAR(100)",
        # Voto
        "ALTER TABLE voto ADD COLUMN funcionario_id INTEGER REFERENCES funcionario(id)",
        "ALTER TABLE voto ADD COLUMN data_hora DATETIME",
        # Eleicao
        "ALTER TABLE eleicao ADD COLUMN unidade VARCHAR(50)",
        "ALTER TABLE eleicao ADD COLUMN data_abertura DATETIME",
        "ALTER TABLE eleicao ADD COLUMN data_encerramento DATETIME",
    ]
    with db.engine.connect() as conn:
        for sql in _alter_stmts:
            try:
                conn.execute(db.text(sql))
                conn.commit()
            except Exception:
                pass

    if not Admin.query.first():
        db.session.add(Admin(
            username='admin',
            password=generate_password_hash('cipa2026'),
        ))
        db.session.commit()

    for unidade in UNIDADES:
        if not Eleicao.query.filter_by(unidade=unidade).first():
            db.session.add(Eleicao(unidade=unidade, status='fechada'))
    db.session.commit()
