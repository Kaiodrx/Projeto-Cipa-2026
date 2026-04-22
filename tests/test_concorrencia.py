"""
Testes de capacidade e configuração de workers.
Cobre: workers configurados no deploy, múltiplos usuários votando, proteção contra voto duplo.
"""
import pytest
from app.extensions import db as _db
from app.models import Funcionario, Voto
from app.constants import UNIDADES

UNIDADE = UNIDADES[0]


# ── Configuração de workers ────────────────────────────────────────────────────

def test_procfile_configurado_com_multiplos_workers():
    with open('Procfile') as f:
        conteudo = f.read()
    assert '--workers' in conteudo, 'Procfile deve definir --workers para suportar acessos simultâneos'


def test_railway_toml_configurado_com_multiplos_workers():
    with open('railway.toml') as f:
        conteudo = f.read()
    assert '--workers' in conteudo, 'railway.toml deve definir --workers para suportar acessos simultâneos'


# ── Múltiplos votantes ─────────────────────────────────────────────────────────

def test_multiplos_funcionarios_votam_e_todos_votos_sao_contabilizados(app, db, candidato, eleicao_aberta):
    """20 funcionários diferentes votam em sequência: todos os votos devem ser contabilizados."""
    TOTAL = 20
    for i in range(TOTAL):
        _db.session.add(Funcionario(
            matricula=f'CONC{i:03d}',
            nome=f'Funcionario Conc {i}',
            unidade=UNIDADE,
            votou=False,
        ))
    _db.session.commit()

    for i in range(TOTAL):
        client = app.test_client()
        resp = client.post('/votacao', data={'matricula': f'CONC{i:03d}', 'unidade': UNIDADE})
        assert resp.status_code == 302, f'Login falhou para CONC{i:03d}'
        resp2 = client.post('/votar', data={'candidato_id': candidato.id})
        assert resp2.status_code == 302, f'Voto falhou para CONC{i:03d}'

    _db.session.expire_all()
    assert Voto.query.filter_by(candidato_id=candidato.id).count() == TOTAL


def test_funcionario_ja_marcado_como_votou_nao_vota_novamente(client, db, funcionario, candidato, eleicao_aberta):
    """Funcionário que já votou não consegue votar de novo, mesmo tentando pelo formulário."""
    funcionario.votou = True
    _db.session.commit()

    resp = client.post('/votacao', data={
        'matricula': funcionario.matricula,
        'unidade': UNIDADE,
    }, follow_redirects=True)

    assert 'já votou' in resp.data.decode()
    assert Voto.query.count() == 0


def test_cada_funcionario_vota_apenas_uma_vez(app, db, candidato, eleicao_aberta):
    """Garante que o mesmo funcionário não consiga registrar dois votos distintos."""
    f = Funcionario(matricula='UNICO01', nome='Funcionario Unico', unidade=UNIDADE, votou=False)
    _db.session.add(f)
    _db.session.commit()

    client = app.test_client()

    # Primeiro voto — deve funcionar
    client.post('/votacao', data={'matricula': 'UNICO01', 'unidade': UNIDADE})
    client.post('/votar', data={'candidato_id': candidato.id})

    # Segunda tentativa — deve ser bloqueada
    resp = client.post('/votacao', data={'matricula': 'UNICO01', 'unidade': UNIDADE},
                       follow_redirects=True)

    assert 'já votou' in resp.data.decode()
    _db.session.expire_all()
    assert Voto.query.filter_by(candidato_id=candidato.id).count() == 1
