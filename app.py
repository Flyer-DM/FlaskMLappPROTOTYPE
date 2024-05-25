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
    kwargs = model_kwargs(load_model(get_prof_num(profession)))
    return render_template('description.html', profession=profession, **kwargs)


if __name__ == '__main__':
    app.run()
