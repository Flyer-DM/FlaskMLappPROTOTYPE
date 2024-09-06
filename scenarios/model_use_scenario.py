from config import GET

from flask import render_template
from flask_login import login_required, current_user


@login_required
def model_for_use():
    """Назначение финализированной модели для использования в калькуляторе"""
    return render_template('model_for_use.html', name=current_user.first_name, surname=current_user.last_name)


model_for_use.methods = [GET]
