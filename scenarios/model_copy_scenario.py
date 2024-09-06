from flask import render_template, request, redirect
from flask_login import login_required, current_user

from config import GET, POST
from domain import db, ModelMeta, ModelHyperparam, ModelParam
from utilities.model_utils import get_prof_name


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


copy_unfinished_model.methods = [POST, GET]
