from datetime import datetime
from .extensions import db


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Candidato(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cargo = db.Column(db.String(100), nullable=False)
    unidade = db.Column(db.String(50), nullable=True)
    foto = db.Column(db.String(500), nullable=True)
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
    dados = db.Column(db.Text, nullable=False)
