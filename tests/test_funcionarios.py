"""
Testes de gerenciamento de funcionários.
Cobre: cadastro com novos campos, edição, matrícula duplicada, remoção, proteção de rotas.
"""
from datetime import date
import pytest
from app.extensions import db as _db
from app.models import Funcionario
from app.constants import UNIDADES

UNIDADE = UNIDADES[0]


# ── Cadastro básico ────────────────────────────────────────────────────────────

def test_adicionar_funcionario_com_sucesso(logged_in_client, db):
    resp = logged_in_client.post('/admin/funcionarios/adicionar', data={
        'matricula': 'MAT999',
        'nome': 'Carlos Teste',
        'unidade': UNIDADE,
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert Funcionario.query.filter_by(matricula='MAT999').first() is not None


def test_adicionar_funcionario_exibe_flash_sucesso(logged_in_client, db):
    resp = logged_in_client.post('/admin/funcionarios/adicionar', data={
        'matricula': 'MAT888',
        'nome': 'Ana Teste',
        'unidade': UNIDADE,
    }, follow_redirects=True)

    assert 'adicionado' in resp.data.decode().lower()


# ── Novos campos ───────────────────────────────────────────────────────────────

def test_adicionar_funcionario_com_novos_campos(logged_in_client, db):
    resp = logged_in_client.post('/admin/funcionarios/adicionar', data={
        'matricula': 'MAT777',
        'nome': 'Funcionario Completo',
        'unidade': UNIDADE,
        'setor': 'TI',
        'cargo': 'Analista',
        'data_admissao': '2020-05-10',
        'data_nascimento': '1990-03-15',
        'ativo': '1',
    }, follow_redirects=True)

    assert resp.status_code == 200
    f = Funcionario.query.filter_by(matricula='MAT777').first()
    assert f is not None
    assert f.setor == 'TI'
    assert f.cargo == 'Analista'
    assert f.data_admissao == date(2020, 5, 10)
    assert f.data_nascimento == date(1990, 3, 15)
    assert f.ativo is True


def test_adicionar_funcionario_inativo(logged_in_client, db):
    logged_in_client.post('/admin/funcionarios/adicionar', data={
        'matricula': 'MAT555',
        'nome': 'Inativo',
        'unidade': UNIDADE,
        'ativo': '0',
    })
    f = Funcionario.query.filter_by(matricula='MAT555').first()
    assert f is not None
    assert f.ativo is False


# ── Edição ─────────────────────────────────────────────────────────────────────

def test_editar_funcionario_atualiza_campos(logged_in_client, db, funcionario):
    resp = logged_in_client.post(
        f'/admin/funcionarios/editar/{funcionario.id}',
        data={
            'matricula': funcionario.matricula,
            'nome': 'Nome Atualizado',
            'unidade': UNIDADE,
            'setor': 'Novo Setor',
            'cargo': 'Novo Cargo',
            'data_admissao': '2015-01-01',
            'data_nascimento': '1988-06-10',
            'ativo': '1',
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    _db.session.expire_all()
    f = Funcionario.query.get(funcionario.id)
    assert f.nome == 'Nome Atualizado'
    assert f.setor == 'Novo Setor'
    assert f.data_admissao == date(2015, 1, 1)


def test_editar_funcionario_exibe_flash_sucesso(logged_in_client, db, funcionario):
    resp = logged_in_client.post(
        f'/admin/funcionarios/editar/{funcionario.id}',
        data={
            'matricula': funcionario.matricula,
            'nome': funcionario.nome,
            'unidade': UNIDADE,
            'ativo': '1',
        },
        follow_redirects=True,
    )
    assert 'atualizado' in resp.data.decode().lower()


# ── Matrícula duplicada ────────────────────────────────────────────────────────

def test_matricula_duplicada_exibe_mensagem_de_erro(logged_in_client, db, funcionario):
    resp = logged_in_client.post('/admin/funcionarios/adicionar', data={
        'matricula': funcionario.matricula,
        'nome': 'Outro Nome',
        'unidade': UNIDADE,
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert 'já cadastrada' in resp.data.decode()


def test_matricula_duplicada_nao_cria_registro(logged_in_client, db, funcionario):
    logged_in_client.post('/admin/funcionarios/adicionar', data={
        'matricula': funcionario.matricula,
        'nome': 'Outro Nome',
        'unidade': UNIDADE,
    })

    total = Funcionario.query.filter_by(matricula=funcionario.matricula).count()
    assert total == 1


# ── Remoção ────────────────────────────────────────────────────────────────────

def test_remover_funcionario_com_sucesso(logged_in_client, db, funcionario):
    fid = funcionario.id
    resp = logged_in_client.get(
        f'/admin/funcionarios/remover/{fid}',
        follow_redirects=True,
    )

    assert resp.status_code == 200
    _db.session.expire_all()
    assert Funcionario.query.get(fid) is None


def test_remover_funcionario_exibe_flash(logged_in_client, db, funcionario):
    resp = logged_in_client.get(
        f'/admin/funcionarios/remover/{funcionario.id}',
        follow_redirects=True,
    )
    assert 'removido' in resp.data.decode().lower()


def test_remover_funcionario_inexistente_retorna_404(logged_in_client, db):
    resp = logged_in_client.get('/admin/funcionarios/remover/99999')
    assert resp.status_code == 404


# ── Listagem e filtros ─────────────────────────────────────────────────────────

def test_listagem_exibe_campos_novos(logged_in_client, db, funcionario):
    resp = logged_in_client.get('/admin/funcionarios')
    body = resp.data.decode()
    # Campos do fixture (setor e cargo)
    assert 'Operações' in body
    assert 'Eletricista' in body


def test_filtro_ativo_retorna_apenas_ativos(logged_in_client, db, funcionario):
    # Adiciona um funcionário inativo com nome único (sem coincidência nos labels do filtro)
    _db.session.add(Funcionario(matricula='INATIVO1', nome='Funcionario Desativado XYZ', unidade=UNIDADE, ativo=False))
    _db.session.commit()

    resp = logged_in_client.get('/admin/funcionarios?ativo=ativo')
    body = resp.data.decode()
    assert 'Maria Santos' in body  # o fixture (ativo=True)
    assert 'Funcionario Desativado XYZ' not in body


# ── Proteção de rota ───────────────────────────────────────────────────────────

def test_adicionar_funcionario_sem_autenticacao_redireciona(client):
    resp = client.post('/admin/funcionarios/adicionar', data={
        'matricula': 'MAT777',
        'nome': 'Invasor',
        'unidade': UNIDADE,
    }, follow_redirects=True)

    assert 'Acesso Administrativo' in resp.data.decode()
    assert Funcionario.query.filter_by(matricula='MAT777').first() is None
