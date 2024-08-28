import re
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from domain import db, User, ModelMeta, ModelMethod, ModelHyperparam
from utilities.model_utils import *
from utilities.train_model import train_catboost, add_model_hyperparams
from utilities.send_email import send_email_assync

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = open('interface_db.txt', 'r').read()
db.init_app(app)


POST = "POST"
GET = "GET"


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите, чтобы получить доступ к этой странице.'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=[GET, POST])
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


@app.route('/connect', methods=[GET, POST])
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


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/index', methods=[GET])
@app.route('/', methods=[GET])
@login_required
def main():
    """
    Первая страница после логина
    :return: загрузка html страницы
    """
    return render_template('main.html', name=current_user.first_name, surname=current_user.last_name)


@app.route('/main', methods=[GET, POST])
@login_required
def models():
    """
    Страница со списком моделей
    :return: загрузка html страницы c переданными параметрами
    """
    if request.method == GET:
        dropdown_list = get_list_of_models()
        return render_template('index.html', name=current_user.first_name, surname=current_user.last_name,
                               dropdown_list=dropdown_list)
    else:
        profession = request.form.get('profession')
        profession_num = get_prof_num(profession)
        prof_models = get_prof_models(profession_num)
        return render_template('index.html', name=current_user.first_name, surname=current_user.last_name,
                               profession=profession, prof_models=prof_models)


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
    return render_template('description.html', name=current_user.first_name, surname=current_user.last_name,
                           profession=profession, lp=learning_plot, ip=importance_plot, **kwargs)


@app.route('/new-model', methods=[GET, POST])
@login_required
def new_model():
    """
    Страница выбора профессии и модели
    :return: загрузка html страницы c переданными параметрами
    """
    dropdown_list = get_list_of_professions()
    if request.method == GET:
        return render_template('new_model.html', name=current_user.first_name, surname=current_user.last_name,
                               dropdown_list=dropdown_list)
    if request.method == POST:
        profession = request.form.get('profession')
        model_type = request.form.get('model')
        return render_template('new_model.html', name=current_user.first_name, surname=current_user.last_name,
                               profession=profession, model=model_type)


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
    return render_template('index.html', name=current_user.first_name, surname=current_user.last_name,
                           dropdown_list=dropdown_list, new_model=True)


@app.route('/new_model_page', methods=[GET, POST])
@app.route('/new_model_page/<int:state>', methods=[GET, POST])
@login_required
def model_creation_page(state: int = None):
    """Страница создания новой модели"""
    user_id, user_name, user_surname = current_user.id, current_user.first_name, current_user.last_name
    all_models = ModelMeta.query.all()
    if request.method == GET:
        return render_template('new_model.html', name=user_name, surname=user_surname, all_models=all_models,
                               get_prof_name=get_prof_name)
    if state == 0:  # создание записи о модели
        prof_list = get_list_of_professions()
        return render_template('new_model.html', name=user_name, surname=user_surname, prof_list=prof_list, state=state)
    elif state == 1:  # обработка создания записи о модели
        model_id = request.form.get('defined_model')
        model: ModelMeta = ModelMeta.query.get(int(model_id if model_id else 0))  # вносятся изменения
        name = request.form.get('model_name')  # может быть изменено значение
        description = request.form.get('model_description')  # может быть изменено значение
        if model:  # если модель уже существует
            model.name = name
            model.description = description
            model.last_changed = user_id
            saved = 2
        else:  # добавляется новая запись о модели
            profession = get_prof_num(request.form.get('profession'))  # не может быть изменено значение
            model = ModelMeta(name=name, description=description, author=user_id, last_changed=user_id,
                              profession=profession)
            saved = 1
            db.session.add(model)
        db.session.commit()
        model_continue = request.form.get('continue')
        if model_continue == 'Продолжить':  # переход на следующий этап создания модели
            return render_template('new_model.html', name=user_name, surname=user_surname, model=model, state=state)
        all_models = ModelMeta.query.all()
        return render_template('new_model.html', name=user_name, surname=user_surname, all_models=all_models,
                               get_prof_name=get_prof_name, saved=saved)
    elif state == 2:  # обработка добавления метода моделирования
        model: ModelMeta = ModelMeta.query.get(int(request.form.get('model')))
        method: ModelMethod = ModelMethod.query.filter_by(name=request.form.get('model_method')).first()
        model.method = method.id
        model.state = state - 1  # состояние модели = 1
        model.last_changed = user_id
        db.session.commit()
        model_continue = request.form.get('continue')
        if model_continue == 'Продолжить':
            return render_template('new_model.html', name=user_name, surname=user_surname, model=model, state=state,
                                   get_prof_name=get_prof_name, method=method.name)
        all_models = ModelMeta.query.all()
        return render_template('new_model.html', name=user_name, surname=user_surname, all_models=all_models,
                               get_prof_name=get_prof_name, saved=1)
    elif state == 3:  # обработка выбора гиперпараметров модели
        model_id = int(request.form.get('model'))
        model: ModelMeta = ModelMeta.query.get(model_id)
        method: ModelMethod = ModelMethod.query.filter_by(id=model.method).first()
        if method.name == 'CatBoostRegressor':
            add_model_hyperparams(db, model_id,
                                  ('epochs', request.form.get('epochs')),
                                  ('early_stop', request.form.get('early_stop')),
                                  ('train_test', request.form.get('train_test').replace(',', '.', 1)),
                                  ('learning_rate', request.form.get('learning_rate').replace(',', '.', 1)),
                                  ('depth', request.form.get('depth')))
        model.state = state - 1  # состояние модели = 2
        model.last_changed = user_id
        db.session.commit()
        model_continue = request.form.get('continue')
        if model_continue == 'Продолжить':
            pass
        all_models = ModelMeta.query.all()
        return render_template('new_model.html', name=user_name, surname=user_surname, all_models=all_models,
                               get_prof_name=get_prof_name, saved=1)


@app.route('/new_model_continue/<int:model_id>/<int:state>', methods=[GET, POST])
@login_required
def continue_with_model(model_id: int, state: int):
    """Продолжение создания модели
    :param model_id: id модели из БД, которую меняем на определённом шаге
    :param state: этап создания модели
    """
    user_id, user_name, user_surname = current_user.id, current_user.first_name, current_user.last_name
    model = ModelMeta.query.get(model_id)
    if state == 0:  # ещё нет записи о таблицы
        return render_template('new_model.html', name=user_name, surname=user_surname, get_prof_name=get_prof_name,
                               state=state, model=model)
    elif state == 1:  # создана запись о модели в БД (название/автор/дата/описание/типовая позиция)
        allowed = any(ModelHyperparam.query.filter_by(model_id=model_id))  # выбраны гиперпараметры? нельзя менять метод
        method: ModelMethod = ModelMethod.query.filter_by(id=model.method).first()
        method = method.name if method else None
        return render_template('new_model.html', name=user_name, surname=user_surname, model=model,
                               get_prof_name=get_prof_name, state=state, method_change_allowed=allowed, method=method)
    elif state == 2:  # выбран метод моделирования
        method: ModelMethod = ModelMethod.query.filter_by(id=model.method).first().name
        return render_template('new_model.html', name=user_name, surname=user_surname, model=model,
                               state=state, get_prof_name=get_prof_name, method=method)


@app.route('/loading', methods=[GET])
@login_required
def loading_page():
    """Заглушка на пустые страницы"""
    return render_template('loading.html', name=current_user.first_name, surname=current_user.last_name)


@app.route('/test_new_model', methods=[GET])
@login_required
def test_new_model():
    """Тестирование новой модели"""
    return render_template('test_new_model.html', name=current_user.first_name, surname=current_user.last_name)


@app.route('/copy_unfinished_model', methods=[GET])
@login_required
def copy_unfinished_model():
    """Копирование модели"""
    return render_template('copy_unfinished_model.html', name=current_user.first_name, surname=current_user.last_name)


@app.route('/model_for_use', methods=[GET])
@login_required
def model_for_use():
    """Назначение финализированной модели для использования в калькуляторе"""
    return render_template('model_for_use.html', name=current_user.first_name, surname=current_user.last_name)


@app.route('/compare-fin-models', methods=[GET, POST])
@login_required
def compare_fin_models():
    """Страница со сравнением финализированных моделей. ТОЛЬКО ИНТЕРФЕЙС.
    GET возвращает страницу с двумя списками финализированных моделей на выбор для сравнения.
    POST возвращает таблицу со сравнением метрик моделей."""
    if request.method == GET:
        return render_template("compare_fin_models.html", name=current_user.first_name, surname=current_user.last_name)
    selected_models = request.form.get('selectedValues')
    selected_models = selected_models.split(',') if selected_models else []
    if not(2 <= len(selected_models) <= 5):
        return render_template("compare_fin_models.html", name=current_user.first_name, surname=current_user.last_name)
    return render_template("compare_fin_models.html", name=current_user.first_name, surname=current_user.last_name,
                           result=True)


@app.route('/check-queue', methods=[GET])
@login_required
def check_queue():
    """Страница с просмотром очереди на обучение. ТОЛЬКО ИНТЕРФЕЙС."""
    return render_template("queue.html", name=current_user.first_name, surname=current_user.last_name)


@app.route('/archive', methods=[GET, POST])
@login_required
def archive_work():
    """Страница для проведения архивации и разархивации моделей и слепков данных. ТОЛЬКО ИНТЕРФЕЙС.
    GET возвращает страницу c выбором типовой позиции и выбором операции (архивация или разархивация).
    POST:
    1)возвращает списки всех моделей и списки всех слепков по значению типовой позиции.
    2)обновляется страница с информацией об архивации/разархивации выбранных значений."""
    dropdown_list = get_list_of_professions()
    if request.method == GET:
        return render_template("archive.html", name=current_user.first_name, surname=current_user.last_name,
                               dropdown_list=dropdown_list)
    elif request.method == POST and (profession := request.form.get('profession')) is not None:
        archive = request.form.get('archive')
        return render_template("archive.html", name=current_user.first_name, surname=current_user.last_name,
                               profession=profession, archive=archive)
    elif request.method == POST and (selectedValues := request.form.get('selectedValues')) is not None:
        return render_template("archive.html", name=current_user.first_name, surname=current_user.last_name,
                               dropdown_list=dropdown_list, archived=True)


if __name__ == '__main__':
    app.run(debug=False)
