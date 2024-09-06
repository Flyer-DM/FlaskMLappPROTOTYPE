import os

import pandas as pd
from itertools import chain

from flask import render_template, request, session
from flask_login import login_required, current_user

from config import GET, POST
from domain import db, ModelMethod, ModelMeta, ModelHyperparam, ModelParam, ModelMetrics, ModelFeatureImportance
from utilities.model_utils import get_prof_name, get_list_of_professions, get_prof_num
from utilities.model_utils import validate_dataset, save_uploaded_dataset, get_all_data_tables
from utilities.train_model import train_model, get_catboost_hyperparams, add_model_hyperparams


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
            if method.name == 'LinearRegression':
                all_datas = get_all_data_tables(model.profession)  # все слепки данных из БД по номеру профессии
                return render_template('new_model.html', name=user_name, surname=user_surname, model=model,
                                       state=state + 1, get_prof_name=get_prof_name, all_datas=all_datas)
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
        if method == 'LinearRegression':
            all_datas = get_all_data_tables(model.profession)  # все слепки данных из БД по номеру профессии
            return render_template('new_model.html', name=user_name, surname=user_surname, model=model,
                                   state=state + 1, get_prof_name=get_prof_name, all_datas=all_datas)
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
    model.state = 4 if model.state < 4 else model.state
    model.last_changed = user_id
    db.session.commit()
    return render_template('new_model.html', name=user_name, surname=user_surname, model=model, state=5)


@login_required
def teach_model(model_id: int):
    """Запуск обучения модели"""
    model: ModelMeta = ModelMeta.query.get(model_id)
    if model.state >= 5:
        return render_template('main.html', name=current_user.first_name, surname=current_user.last_name,
                               train='not')
    model.state = 5
    model.retrained += 1
    model.last_changed = current_user.id
    filename, n, rmse, mape, dev_metrics, feature_importances = train_model(model_id)
    model.model_file = filename
    metrics: ModelMetrics = ModelMetrics(model_id=model_id, n=n, rmse=rmse, mape=mape, **dev_metrics)
    db.session.add(metrics)
    metrics_id = ModelMetrics.query.filter_by(model_id=model_id).first().id
    for i, elem in enumerate(feature_importances.items(), 1):
        name = elem[0]
        if name == 'ыеар':
            name = 'Год'
        importance: ModelFeatureImportance = ModelFeatureImportance(model_metrics_id=metrics_id,
                                                                    top=i, name=name, value=elem[1])
        db.session.add(importance)
    db.session.commit()
    return render_template('main.html', name=current_user.first_name, surname=current_user.last_name, train='started')


upload_dataset.methods = [POST]
save_upload_data.methods = [POST]
model_creation_page.methods = [GET, POST]
continue_with_model.methods = [GET, POST]
set_data_table_for_model.methods = [GET]
set_params_for_model.methods = [POST]
teach_model.methods = [GET]
