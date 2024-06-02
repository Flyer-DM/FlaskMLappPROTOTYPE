import re
from flask import Flask, render_template, request
from utilities.model_utils import *
from utilities.train_model import train_catboost

app = Flask(__name__)


POST = "POST"
GET = "GET"


@app.route('/index', methods=[GET, POST])
@app.route('/', methods=[GET, POST])
def main():
    """
    Главная страница программы
    :return: загрузка html страницы c переданными параметрами
    """
    if request.method == GET:
        dropdown_list = get_list_of_models()
        return render_template('index.html', dropdown_list=dropdown_list)
    else:
        profession = request.form.get('profession')
        profession_num = get_prof_num(profession)
        prof_models = get_prof_models(profession_num)
        return render_template('index.html', profession=profession, prof_models=prof_models)


@app.route('/model-description', methods=[POST])
def model_description():
    """
    Страница с описанием версии модели выбранной профессии
    :return: загрузка html страницы c переданными параметрами
    """
    model_ver = request.form.get('model_ver')
    profession_num = int(re.search(r'(?<=/)\d+(?=/)', model_ver).group()[0])
    profession = get_prof_name(profession_num)
    model = load_model(model_ver)
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
    """
    Главная страница после сохранения версии модели
    :return: загрузка html страницы c переданными параметрами
    """
    dropdown_list = get_list_of_models()
    profession_num = get_prof_num(request.form.get('profession'))
    model_type = request.form.get('model')
    epochs = int(request.form.get('epochs'))
    early_stop = int(request.form.get('early_stop'))
    train_test = float(request.form.get('train_test').replace(',', '.', 1))
    learning_rate = float(request.form.get('learning_rate').replace(',', '.', 1))
    depth = int(request.form.get('depth'))
    file = request.files['file']
    if model_type == 'Catboost':
        train_catboost(file, profession_num, epochs, early_stop, train_test, learning_rate, depth)
    return render_template('index.html', dropdown_list=dropdown_list, new_model=True)


if __name__ == '__main__':
    app.run(debug=True)
