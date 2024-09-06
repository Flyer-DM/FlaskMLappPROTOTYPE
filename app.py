import atexit
from config import GET, app
from scenarios import *
from flask import render_template
from flask_login import login_required, current_user
from utilities.file_utils import cleanup

# сценарий логина
app.add_url_rule('/login', view_func=login)
app.add_url_rule('/logout', view_func=logout)
app.add_url_rule('/connect', view_func=connect_to_admin)
# сценарий обучения модели
app.add_url_rule('/upload-dataset', view_func=upload_dataset)
app.add_url_rule('/save-uploaded-dataset', view_func=save_upload_data)
app.add_url_rule('/new_model_page', view_func=model_creation_page)
app.add_url_rule('/new_model_page/<int:state>', view_func=model_creation_page)
app.add_url_rule('/new_model_continue/<int:model_id>/<int:state>', view_func=continue_with_model)
app.add_url_rule('/set-data-table/<int:model_id>/<string:table_name>', view_func=set_data_table_for_model)
app.add_url_rule('/set-model-params/<int:model_id>', view_func=set_params_for_model)
app.add_url_rule('/teach_model/<int:model_id>', view_func=teach_model)
# сценарий копирования незавершённой модели
app.add_url_rule('/copy_unfinished_model', view_func=copy_unfinished_model)
# сценарий просмотра характеристик незавершённых моделей
app.add_url_rule('/incomplete_model', view_func=incomplete_model)
app.add_url_rule('/incomplete_model/<int:model_id>', view_func=incomplete_model)
app.add_url_rule('/delete_model/<int:model_id>', view_func=delete_model)
# сценарий тестирования обученных моделей на новых данных
app.add_url_rule('/test_new_model', view_func=test_new_model)
# сценарий назначения финализированной модели
app.add_url_rule('/model_for_use', view_func=model_for_use)
# сценарий сравнения финализированных моделей
app.add_url_rule('/compare-fin-models', view_func=model_for_use)
# сценарий просмотра очереди на обучение
app.add_url_rule('/check-queue', view_func=check_queue)
# сценарий архивации/разархивации данных/моделей в холодное хранилище
app.add_url_rule('/archive', view_func=check_queue)


atexit.register(cleanup)


@app.route('/index', methods=[GET])
@app.route('/', methods=[GET])
@login_required
def main():
    """Первая страница после логина со ссылками на все пользовательские сценарии"""
    return render_template('main.html', name=current_user.first_name, surname=current_user.last_name)


@app.route('/loading', methods=[GET])
@login_required
def loading_page():
    """Заглушка на пустые страницы"""
    return render_template('loading.html', name=current_user.first_name, surname=current_user.last_name)


if __name__ == '__main__':
    app.run(debug=False)
