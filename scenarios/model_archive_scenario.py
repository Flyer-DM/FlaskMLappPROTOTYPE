from config import GET, POST

from flask import render_template, request
from flask_login import login_required, current_user

from utilities.model_utils import get_list_of_professions


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


archive_work.methods = [GET, POST]
