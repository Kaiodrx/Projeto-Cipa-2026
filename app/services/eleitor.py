"""
Validação centralizada do eleitor antes do acesso à votação.

Mantém a lógica fora da rota para facilitar testes e futura evolução
(ex.: segundo fator, bloqueio por tentativas, etc.).
"""
from datetime import date

from ..models import Funcionario, Eleicao

_ERRO_DADOS = (
    'Dados não conferem. Verifique matrícula, unidade e data de nascimento.'
)


def validar_eleitor(matricula: str, unidade: str, data_nascimento_str: str):
    """
    Valida todas as condições para um funcionário acessar a votação.

    Retorna (funcionario, None) em caso de sucesso.
    Retorna (None, mensagem_de_erro) em caso de falha.

    A mesma mensagem genérica é usada para matrícula inválida, unidade
    incorreta e data de nascimento errada — evitando enumeração de usuários.
    """
    try:
        data_nasc = date.fromisoformat(data_nascimento_str.strip())
    except (ValueError, AttributeError):
        return None, _ERRO_DADOS

    funcionario = Funcionario.query.filter_by(matricula=matricula).first()

    if not funcionario or funcionario.unidade != unidade:
        return None, _ERRO_DADOS

    if not funcionario.data_nascimento or funcionario.data_nascimento != data_nasc:
        return None, _ERRO_DADOS

    if not funcionario.ativo:
        return None, 'Você não está habilitado a votar nesta eleição.'

    if funcionario.votou:
        return None, 'Você já votou nesta eleição.'

    eleicao = Eleicao.query.filter_by(unidade=unidade).first()
    if not eleicao or eleicao.status != 'aberta':
        return None, 'A eleição desta unidade não está aberta no momento.'

    return funcionario, None
