from config import POST

from flask import render_template
from flask_login import login_required, current_user


@login_required
def check_queue():
    """Страница с просмотром очереди на обучение. ТОЛЬКО ИНТЕРФЕЙС."""
    return render_template("queue.html", name=current_user.first_name, surname=current_user.last_name)


check_queue.methods = [POST]
