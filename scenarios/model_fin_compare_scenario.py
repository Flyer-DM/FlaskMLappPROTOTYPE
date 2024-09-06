from config import GET, POST

from flask import render_template, request
from flask_login import login_required, current_user


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


compare_fin_models.methods = [GET, POST]
