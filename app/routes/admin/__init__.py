from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

from . import auth, dashboard, candidatos, funcionarios, eleicao, apuracao, relatorios, participacao, resultado, historico  # noqa
