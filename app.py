from flask import Flask, render_template, request
from utilities.model_utils import *

app = Flask(__name__)


POST = "POST"
GET = "GET"


@app.route('/index', methods=[GET])
@app.route('/', methods=[GET])
def main():
    """
    Главная страница программы
    :return: загрузка html страницы c переданными параметрами
    """
    dropdown_list = get_list_of_models()
    return render_template('index.html', dropdown_list=dropdown_list)


@app.route('/model-description', methods=[POST])
def model_description():
    """
    Страница с описанием модели выбранной модели
    :return: загрузка html страницы c переданными параметрами
    """
    profession = request.form.get('profession')
    profession_num = get_prof_num(profession)
    model = load_model(profession_num)
    kwargs = model_kwargs(model)
    # График обучения
    get_learning_plot(model)
    # График важности признаков
    get_importance_plot(profession_num, model)
    return render_template('description.html', profession=profession, **kwargs)


@app.route('/new-model', methods=[GET, POST])
def new_model():
    """
    Страница выбора профессии и модели
    :return: загрузка html страницы c переданными параметрами
    """
    dropdown_list = get_list_of_professions()
    if request.method == GET:
        return render_template('new_model.html', dropdown_list=dropdown_list)
    if request.method == POST:
        profession = request.form.get('profession')
        model_type = request.form.get('model')
        return render_template('new_model.html', profession=profession, model=model_type)


@app.route('/upload-dataset', methods=[POST])
def new_model_train():
    dropdown_list = get_list_of_models()
    profession_num = get_prof_num(request.form.get('profession'))
    model_type = request.form.get('model')
    file = request.files['file']
    if model_type == 'Catboost':
        train_catboost(file, profession_num)
    return render_template('index.html', dropdown_list=dropdown_list, new_model=True)


if __name__ == '__main__':
    app.run(debug=True)
