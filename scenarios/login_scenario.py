from flask import render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user

from config import app, GET, POST
from domain import User
from utilities.send_email import send_email_assync


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите, чтобы получить доступ к этой странице.'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def login():
    if request.method == POST:
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main'))
        else:
            flash('Неверный логин/пароль')
            return render_template('login.html', cantlogin=True)
    return render_template('login.html')


def connect_to_admin():
    """
    Асинхронная отправка сообщения на почту в случае, если пользователь не может войти в систему
    :return: загрузка html страницы
    """
    if request.method == GET:
        return render_template('login.html', connect=True)
    send_email_assync(request.form.get("name"), request.form.get("surname"), request.form.get("email"),
                      request.form.get("add"))
    return render_template('login.html', sendmessage=True)


@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


login.methods = [POST, GET]
connect_to_admin.methods = [POST, GET]
