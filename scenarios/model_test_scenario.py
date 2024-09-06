from config import GET

from flask import render_template
from flask_login import login_required, current_user


@login_required
def test_new_model():
    """Тестирование новой модели"""
    return render_template('test_new_model.html', name=current_user.first_name, surname=current_user.last_name)


test_new_model.methods = [GET]
