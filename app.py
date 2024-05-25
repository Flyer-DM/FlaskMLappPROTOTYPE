from flask import Flask, render_template, request
from utilities.model_utils import *

app = Flask(__name__)


POST = "POST"
GET = "GET"


@app.route('/index', methods=[GET])
@app.route('/', methods=[GET])
def main():
    dropdown_list = get_list_of_models()
    return render_template('index.html', dropdown_list=dropdown_list)


@app.route('/model-description', methods=[POST])
def model_description():
    profession = request.form.get('profession')
    profession_num = get_prof_num(profession)
    model = load_model(profession_num)
    kwargs = model_kwargs(model)
    # График обучения
    get_learning_plot(model)
    # График важности признаков
    get_importance_plot(profession_num, model)
    return render_template('description.html', profession=profession, **kwargs)


if __name__ == '__main__':
    app.run(debug=True)
