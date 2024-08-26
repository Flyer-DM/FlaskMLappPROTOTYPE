import re
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from utilities.model_utils import *
from utilities.train_model import train_catboost

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

app.secret_key = 'your_secret_key'  

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите, чтобы получить доступ к этой странице.'

users = {'admin': generate_password_hash('password')}


class User(UserMixin):
    def __init__(self, username):
        self.id = username


@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id)
    return None


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and check_password_hash(users[username], password):
            user = User(username)
            login_user(user)
            return redirect(url_for('main'))
        else:
            flash('Неверный логин/пароль')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


POST = "POST"
GET = "GET"


@app.route('/index', methods=[GET])
@app.route('/', methods=[GET])
@login_required
def main():
    """
    Первая страница после логина
    :return: загрузка html страницы
    """
    return render_template('main.html')


@app.route('/main', methods=[GET, POST])
@login_required
def models():
    """
    Страница со списком моделей
    :return: загрузка html страницы c переданными параметрами
    """
    if request.method == GET:
        dropdown_list = get_list_of_models()
        return render_template('index.html', dropdown_list=dropdown_list)
    else:
        profession = request.form.get('profession')
        profession_num = get_prof_num(profession)
        prof_models = get_prof_models(profession_num)
        return render_template('index.html', profession=profession, prof_models=prof_models)


@app.route('/model-description', methods=[POST])
@login_required
def model_description():
    """
    Страница с описанием версии модели выбранной профессии
    :return: загрузка html страницы c переданными параметрами
    """
    model_ver = request.form.get('model_ver')
    profession_num = int(re.search(r'(?<=/)\d+(?=/)', model_ver).group()[0])
    profession = get_prof_name(profession_num)
    model = load_model(model_ver)
    kwargs = model_kwargs(model)
    # График обучения
    learning_plot = get_learning_plot(model)
    # График важности признаков
    importance_plot = get_importance_plot(profession_num, model)
    return render_template('description.html', profession=profession, lp=learning_plot, ip=importance_plot,
                           **kwargs)


@app.route('/new-model', methods=[GET, POST])
@login_required
def new_model():
    """
    Страница выбора профессии и модели
    :return: загрузка html страницы c переданными параметрами
    """
    dropdown_list = get_list_of_professions()
    if request.method == GET:
        return render_template('new_model.html', dropdown_list=dropdown_list)
    if request.method == POST:
        profession = request.form.get('profession')
        model_type = request.form.get('model')
        return render_template('new_model.html', profession=profession, model=model_type)


@app.route('/upload-dataset', methods=[POST])
@login_required
def new_model_train():
    """
    Главная страница после сохранения версии модели
    :return: загрузка html страницы c переданными параметрами
    """
    dropdown_list = get_list_of_models()
    profession_num = get_prof_num(request.form.get('profession'))
    model_type = request.form.get('model')
    epochs = int(request.form.get('epochs'))
    early_stop = int(request.form.get('early_stop'))
    train_test = float(request.form.get('train_test').replace(',', '.', 1))
    learning_rate = float(request.form.get('learning_rate').replace(',', '.', 1))
    depth = int(request.form.get('depth'))
    file = request.files['file']
    if model_type == 'CatboostRegressor':
        train_catboost(file, profession_num, epochs, early_stop, train_test, learning_rate, depth)
    return render_template('index.html', dropdown_list=dropdown_list, new_model=True)

@app.route('/new_model_page', methods=[GET])
@login_required
def new_model_page():
    """Страница создания модели, обучения модели"""
    return render_template('new_model.html')

@app.route('/loading', methods=[GET])
@login_required
def loading_page():
    """Заглушка на пустые страницы"""
    return render_template('loading.html')


if __name__ == '__main__':
    app.run(debug=False)
