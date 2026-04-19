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
            password=generate_password_hash('cipa2026'),
        ))
        db.session.commit()

    for unidade in UNIDADES:
        if not Eleicao.query.filter_by(unidade=unidade).first():
            db.session.add(Eleicao(unidade=unidade, status='fechada'))
    db.session.commit()
