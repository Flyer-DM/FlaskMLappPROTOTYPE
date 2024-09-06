import os

from flask import render_template, redirect, url_for
from flask_login import login_required, current_user

from config import GET, POST
from domain import db, ModelMeta, ModelHyperparam, ModelParam, ModelMetrics, ModelFeatureImportance
from utilities.model_utils import get_prof_name, get_importance_plot


@login_required
def incomplete_model(model_id: int = None):
    """Страница открытия незавершённой модели и подробностей о модели"""
    user_name, user_surname = current_user.first_name, current_user.last_name
    all_models = ModelMeta.query.all()
    if model_id is not None:
        model = ModelMeta.query.get(model_id)
        hyperparams = ModelHyperparam.query.filter_by(model_id=model_id).all()
        params = ModelParam.query.filter_by(model_id=model_id).first()
        metrics = ModelMetrics.query.filter_by(model_id=model_id).first()
        importance_plot = None
        if metrics:
            importances = ModelFeatureImportance.query.filter_by(model_metrics_id=metrics.id).all()
            importance_plot = get_importance_plot(importances)
        return render_template('incomplete_model.html', name=user_name, surname=user_surname, model=model,
                               get_prof_name=get_prof_name, show_table=False, hyperparams=hyperparams, params=params,
                               metrics=metrics, ip=importance_plot)
    return render_template('incomplete_model.html', name=user_name, surname=user_surname, all_models=all_models,
                           get_prof_name=get_prof_name, show_table=True)


@login_required
def delete_model(model_id: int):
    """Удаление модели и связанных записей"""
    try:
        model: ModelMeta = db.session.get(ModelMeta, model_id)
        if (file_to_del := model.model_file) is not None:  # если модель уже обучена, нужно удалить файл модели
            try:
                os.remove(file_to_del)
            except Exception:
                pass
        db.session.delete(model)
        db.session.commit()
    except Exception as e:
        print(f'Ошибка удаления: {e}')
        db.session.rollback()
    return redirect(url_for('incomplete_model'))


incomplete_model.methods = [GET]
delete_model.methods = [POST]
