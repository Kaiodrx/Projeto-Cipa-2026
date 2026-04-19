"""
Testes de autenticação do painel administrativo.
Cobre: login com sucesso, erros de credencial, proteção de rotas e logout.
"""
import pytest


# ── Login ──────────────────────────────────────────────────────────────────────

def test_login_sucesso_redireciona_para_dashboard(client):
    resp = client.post('/admin/login', data={
        'username': 'admin',
        'password': 'cipa2026',
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert 'Painel de Controle' in resp.data.decode()


def test_login_senha_incorreta_exibe_mensagem_de_erro(client):
    resp = client.post('/admin/login', data={
        'username': 'admin',
        'password': 'senha_errada',
    }, follow_redirects=True)

    assert resp.status_code == 200
    html = resp.data.decode()
    assert 'incorretos' in html
    # Usuário permanece na tela de login
    assert 'Acesso Administrativo' in html


def test_login_usuario_inexistente_exibe_mensagem_de_erro(client):
    resp = client.post('/admin/login', data={
        'username': 'usuario_fantasma',
        'password': 'qualquer',
    }, follow_redirects=True)

    assert resp.status_code == 200
    html = resp.data.decode()
    assert 'incorretos' in html
    assert 'Acesso Administrativo' in html


def test_login_campos_vazios_nao_autentica(client):
    resp = client.post('/admin/login', data={
        'username': '',
        'password': '',
    }, follow_redirects=True)

    # Formulário exige campos obrigatórios — não deve chegar ao dashboard
    assert resp.status_code == 200
    assert 'Painel de Controle' not in resp.data.decode()


# ── Proteção de rotas ──────────────────────────────────────────────────────────

def test_dashboard_sem_autenticacao_redireciona_para_login(client):
    resp = client.get('/admin', follow_redirects=True)

    assert resp.status_code == 200
    assert 'Acesso Administrativo' in resp.data.decode()


def test_candidatos_sem_autenticacao_redireciona_para_login(client):
    resp = client.get('/admin/candidatos', follow_redirects=True)

    assert resp.status_code == 200
    assert 'Acesso Administrativo' in resp.data.decode()


def test_funcionarios_sem_autenticacao_redireciona_para_login(client):
    resp = client.get('/admin/funcionarios', follow_redirects=True)

    assert resp.status_code == 200
    assert 'Acesso Administrativo' in resp.data.decode()


# ── Logout ─────────────────────────────────────────────────────────────────────

def test_logout_encerra_sessao_e_redireciona_para_login(logged_in_client):
    # Confirma acesso antes do logout
    resp = logged_in_client.get('/admin')
    assert resp.status_code == 200

    # Realiza logout
    resp = logged_in_client.get('/admin/logout', follow_redirects=True)
    assert resp.status_code == 200
    assert 'Acesso Administrativo' in resp.data.decode()

    # Tenta acessar área protegida após logout — deve redirecionar
    resp = logged_in_client.get('/admin', follow_redirects=True)
    assert 'Acesso Administrativo' in resp.data.decode()
