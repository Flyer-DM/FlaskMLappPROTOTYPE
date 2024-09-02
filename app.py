import os
import re
import atexit
from itertools import chain
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from domain import db, User, ModelMeta, ModelMethod, ModelHyperparam, ModelParam
from utilities.model_utils import *
from utilities.file_utils import cleanup
from utilities.train_model import train_model, add_model_hyperparams, get_catboost_hyperparams
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


atexit.register(cleanup)


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


@app.route('/upload-dataset', methods=[POST])
@login_required
def upload_dataset():
    """
    Главная страница после сохранения версии модели
    :return: загрузка html страницы c переданными параметрами
    """
    user_name, user_surname = current_user.first_name, current_user.last_name
    model: ModelMeta = ModelMeta.query.get(int(request.form.get('model')))
    file = request.files['file']
    e, valid, dataset = validate_dataset(file)
    if not valid:
        return render_template('new_model.html', name=user_name, surname=user_surname, model=model, state=3, e=e)
    filename = f'./datasets/temp_data_{current_user.username}.csv'
    dataset.to_csv(filename)
    session['temp_file_path'] = filename
    return render_template('new_model.html', name=user_name, surname=user_surname, model=model, state=3, valid=valid,
                           dataset=dataset)


@app.route('/save-uploaded-dataset', methods=[POST])
@login_required
def save_upload_data():
    """Сохранение загруженного пользователем датасета (csv) в БД
    :return: загрузка html страницы c переданными параметрами"""
    save = request.form.get('save-data')
    user_name, user_surname = current_user.first_name, current_user.last_name
    model: ModelMeta = ModelMeta.query.get(int(request.form.get('model')))
    temp_file = session.pop('temp_file_path', None)
    if save == 'Да':
        dataset = pd.read_csv(temp_file)
        result = save_uploaded_dataset(dataset, model.profession)
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)  # Удаляем временный файл
        all_datas = get_all_data_tables(model.profession)
        return render_template('new_model.html', name=user_name, surname=user_surname, model=model, state=3, saved=True,
                               get_prof_name=get_prof_name, save_result=result, all_datas=all_datas)
    if temp_file and os.path.exists(temp_file):
        os.remove(temp_file)  # Удаляем временный файл
    return render_template('new_model.html', name=user_name, surname=user_surname, model=model, state=3, saved=False,
                           get_prof_name=get_prof_name)


@app.route('/new_model_page', methods=[GET, POST])
@app.route('/new_model_page/<int:state>', methods=[GET, POST])
@login_required
def model_creation_page(state: int = None):
    """Страница создания новой модели"""
    user_id, user_name, user_surname = current_user.id, current_user.first_name, current_user.last_name
    all_models = ModelMeta.query.all()
    if request.method == GET:  # список всех незавершённых моделей
        return render_template('new_model.html', name=user_name, surname=user_surname, all_models=all_models,
                               get_prof_name=get_prof_name)
    if state == 0:  # страница для создания записи о новой модели
        prof_list = get_list_of_professions()
        return render_template('new_model.html', name=user_name, surname=user_surname, prof_list=prof_list, state=state)
    elif state == 1:  # обработка создания записи о модели (автоматически state=0)
        model_id = request.form.get('defined_model')  # получение id модели, если уже есть запись
        model: ModelMeta = ModelMeta.query.get(model_id if model_id else 0)  # вносятся изменения
        name = request.form.get('model_name')  # может быть изменено значение
        description = request.form.get('model_description')  # может быть изменено значение
        if model:  # если модель уже существует (меняются параметры)
            model.name = name
            model.description = description
            model.last_changed = user_id
        else:  # добавляется новая запись о модели
            profession = get_prof_num(request.form.get('profession'))  # не может быть изменено значение
            model = ModelMeta(name=name, description=description, author=user_id, last_changed=user_id,
                              profession=profession)
            db.session.add(model)
        db.session.commit()
        model_continue = request.form.get('continue')
        if model_continue == 'Продолжить':  # переход на следующий этап создания модели
            allowed = any(ModelHyperparam.query.filter_by(model_id=model_id))  # есть ли уже гиперпараметры?
            method: ModelMethod = ModelMethod.query.filter_by(id=model.method).first()
            method = method.name if method else None
            return render_template('new_model.html', name=user_name, surname=user_surname, model=model, state=state,
                                   method_change_allowed=allowed, method=method)
        return render_template('new_model.html', name=user_name, surname=user_surname, all_models=ModelMeta.query.all(),
                               get_prof_name=get_prof_name, saved=1)
    elif state == 2:  # обработка добавления метода моделирования
        model: ModelMeta = ModelMeta.query.get(model_id := request.form.get('model'))
        method: ModelMethod = ModelMethod.query.filter_by(name=request.form.get('model_method')).first()
        model.method = method.id
        model.state = state - 1  # состояние модели = 1
        model.last_changed = user_id
        db.session.commit()
        model_continue = request.form.get('continue')
        if model_continue == 'Продолжить':
            if any(ModelHyperparam.query.filter_by(model_id=model_id).all()):  # если уже есть гиперпараметры
                if method.name == 'CatBoostRegressor':
                    hyperparams = get_catboost_hyperparams(model_id)
                    return render_template('new_model.html', name=user_name, surname=user_surname, model=model,
                                           state=state, get_prof_name=get_prof_name, method=method.name,
                                           catboost_params=hyperparams)
            return render_template('new_model.html', name=user_name, surname=user_surname, model=model, state=state,
                                   get_prof_name=get_prof_name, method=method.name)
        all_models = ModelMeta.query.all()
        return render_template('new_model.html', name=user_name, surname=user_surname, all_models=all_models,
                               get_prof_name=get_prof_name, saved=1)
    elif state == 3:  # обработка выбора гиперпараметров модели
        model_id = request.form.get('model')
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
            all_datas = get_all_data_tables(model.profession)  # все слепки данных из БД по номеру профессии
            return render_template('new_model.html', name=user_name, surname=user_surname, model=model, state=state,
                                   get_prof_name=get_prof_name, all_datas=all_datas)
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
    model: ModelMeta = ModelMeta.query.get(model_id)
    if model.state == 5:  # если модель уже обучена нельзя перейти на предыдущие шаги
        return render_template('new_model.html', name=user_name, surname=user_surname, model=model, state=5,
                               trained=True)
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
        if any(ModelHyperparam.query.filter_by(model_id=model_id).all()):  # если уже есть гиперпараметры
            if method == 'CatBoostRegressor':
                hyperparams = get_catboost_hyperparams(model_id)
                return render_template('new_model.html', name=user_name, surname=user_surname, model=model,
                                       state=state, get_prof_name=get_prof_name, method=method,
                                       catboost_params=hyperparams)
        return render_template('new_model.html', name=user_name, surname=user_surname, model=model,
                               state=state, get_prof_name=get_prof_name, method=method)
    elif state == 3:  # выбраны гиперпараметры модели
        all_datas = get_all_data_tables(model.profession)
        return render_template('new_model.html', name=user_name, surname=user_surname, model=model, state=state,
                               get_prof_name=get_prof_name, all_datas=all_datas)
    elif state == 4:  # выбран слепок данных
        mf: ModelParam = ModelParam.query.filter_by(model_id=model_id).first()
        regions = chain.from_iterable(pd.read_csv('./datasets/regions.csv', usecols=['region_name']).values.tolist())
        return render_template('new_model.html', name=user_name, surname=user_surname, model=model, state=state,
                               regions=list(regions), mf=mf)
    elif state == 5:
        return render_template('new_model.html', name=user_name, surname=user_surname, model=model, state=5)


@app.route('/set-data-table/<int:model_id>/<string:table_name>', methods=[GET])
@login_required
def set_data_table_for_model(model_id: int, table_name: str):  # state = 4 (сохранение таблицы данных)
    """Установка имени таблицы для обучения модели"""
    user_name, user_surname, user_id = current_user.first_name, current_user.last_name, current_user.id
    model: ModelMeta = ModelMeta.query.get(model_id)
    model.train_table = table_name
    model.state = model.state if model.state > 3 else 3
    model.last_changed = user_id
    db.session.commit()
    regions = chain.from_iterable(pd.read_csv('./datasets/regions.csv', usecols=['region_name']).values.tolist())
    return render_template('new_model.html', name=user_name, surname=user_surname, model=model,
                           get_prof_name=get_prof_name, state=model.state + 1, regions=list(regions))


@app.route('/set-model-params/<int:model_id>', methods=[POST])
@login_required
def set_params_for_model(model_id: int):  # state = 5 (установка параметров (фильтров) модели)
    """Установка параметров (фильтров) обучения: вахта, частичная занятость, уровень опыта, регион"""
    user_name, user_surname, user_id = current_user.first_name, current_user.last_name, current_user.id
    model: ModelMeta = ModelMeta.query.get(model_id)
    is_vahta = bool(int(request.form.get('is_vahta')))
    is_parttime = bool(int(request.form.get('is_parttime')))
    experience_id = int(request.form.get('experience_id'))
    region_name = request.form.get('region_name')
    if (model_param := ModelParam.query.filter_by(model_id=model_id).first()) is not None:  # параметры уже настроены:
        model_param.is_vahta = is_vahta
        model_param.is_parttime = is_parttime
        model_param.experience_id = experience_id
        model_param.region_name = region_name
    else:  # сохраняются новые параметры модели
        model_params = ModelParam(model_id=model_id, is_vahta=is_vahta, is_parttime=is_parttime,
                                  experience_id=experience_id, region_name=region_name)
        db.session.add(model_params)
    model.last_changed = user_id
    db.session.commit()
    return render_template('new_model.html', name=user_name, surname=user_surname, model=model, state=model.state + 1)


@app.route('/teach_model/<int:model_id>', methods=[GET])
@login_required
def teach_model(model_id: int):
    """Запуск обучения модели"""
    model: ModelMeta = ModelMeta.query.get(model_id)
    model.state = 5
    model.retrained += 1
    model.last_changed = current_user.id
    model.model_file = train_model(model_id)
    db.session.commit()
    return render_template('main.html', name=current_user.first_name, surname=current_user.last_name, train='started')


@app.route('/incomplete_model', methods=[GET])
@app.route('/incomplete_model/<int:model_id>', methods=[GET])
@login_required
def incomplete_model(model_id: int = None):
    """Страница открытия незавершённой модели и подробностей о модели"""
    user_name, user_surname = current_user.first_name, current_user.last_name
    all_models = ModelMeta.query.all()
    if model_id is not None:
        model = ModelMeta.query.get(model_id)
        hyperparams = ModelHyperparam.query.filter_by(model_id=model_id).all()
        params = ModelParam.query.filter_by(model_id=model_id).first()
        return render_template('incomplete_model.html', name=user_name, surname=user_surname, model=model,
                               get_prof_name=get_prof_name, show_table=False, hyperparams=hyperparams, params=params)
    return render_template('incomplete_model.html', name=user_name, surname=user_surname, all_models=all_models,
                           get_prof_name=get_prof_name, show_table=True)


@app.route('/delete_model/<int:model_id>', methods=['POST'])
@login_required
def delete_model(model_id: int):
    """Удаление модели и связанных записей"""
    try:
        model: ModelMeta = db.session.get(ModelMeta, model_id)
        if (file_to_del := model.model_file) is not None:  # если модель уже обучена, нужно удалить файл модели
            os.remove(file_to_del)
        db.session.delete(model)
        db.session.commit()
    except Exception as e:
        print(f'Ошибка удаления: {e}')
        db.session.rollback()
    return redirect(url_for('incomplete_model'))


@app.route('/copy_unfinished_model', methods=[GET, POST])
@login_required
def copy_unfinished_model():
    """Копирование незавершённой модели с новыми данными"""
    user_id, user_name, user_surname = current_user.id, current_user.first_name, current_user.last_name
    if request.method == GET:
        all_models = ModelMeta.query.all()  
        return render_template('copy_unfinished_model.html', name=user_name, surname=user_surname,
                               all_models=all_models)
    if request.method == POST:
        model_id = request.form.get('model')
        # Создаем копию модели
        original_model: ModelMeta = ModelMeta.query.get(model_id)
        new_model = ModelMeta(
            name=original_model.name + " (копия)",
            description=original_model.description,
            author=user_id,
            last_changed=user_id,
            profession=original_model.profession,
            method=original_model.method,
            state=original_model.state if original_model.state < 5 else 4,  # если копия обученной модели
            train_table=original_model.train_table,
            orig=original_model.id
        )
        db.session.add(new_model)
        # Создаём копию гиперпараметров
        model_hyperparams = ModelHyperparam.query.filter_by(model_id=model_id)
        for param in model_hyperparams:
            new_param = ModelHyperparam(
                model_id=new_model.id,
                name=param.name,
                value=param.value
            )
            db.session.add(new_param)
        # Создаём копию параметров
        param: ModelParam = ModelParam.query.filter_by(model_id=model_id).first()
        if param:
            new_param = ModelParam(
                model_id=new_model.id,
                is_vahta=param.is_vahta,
                is_parttime=param.is_parttime,
                experience_id=param.experience_id,
                region_name=param.region_name,
            )
            db.session.add(new_param)
        db.session.commit()
        if original_model.state < 5:
            return redirect('/index')
        return render_template('new_model.html', name=user_name, surname=user_surname, get_prof_name=get_prof_name,
                               state=0, model=new_model)


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
