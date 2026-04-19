from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from . import admin_bp
from ...models import Admin


@admin_bp.route('/login', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            session['admin_id'] = admin.id
            return redirect(url_for('admin.dashboard'))
        flash('Usuário ou senha incorretos.', 'danger')
    return render_template('login_admin.html')


@admin_bp.route('/logout')
def logout_admin():
    session.pop('admin_id', None)
    return redirect(url_for('admin.login_admin'))
