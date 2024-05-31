import os
import glob
import json
import pandas as pd
import matplotlib.pyplot as plt
from catboost import CatBoostRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from datetime import datetime
from werkzeug.datastructures import FileStorage

MODELS_PATH = 'ml_models'
DATASETS_PATH = 'datasets'


def train_catboost(dataset_name: FileStorage, profession_num: int):
    data = pd.read_csv(dataset_name, index_col='id')
    target = 'new_salary'

    data = data.drop(columns=['salary_from_rub'], errors='ignore')

    categorical_columns = []
    for col in data.columns[data.dtypes == object]:
        data[col] = LabelEncoder().fit_transform(data[col].values)
        categorical_columns.append(col)
    features = [col for col in data.columns if col not in [target]]
    cat_idxs = [i for i, f in enumerate(features) if f in categorical_columns]

    for col in data.columns[data.dtypes == bool]:
        data[col] = data[col].astype(int)

    model = CatBoostRegressor(iterations=3000, loss_function='RMSE',
                              early_stopping_rounds=100)

    x = data.drop(columns=['new_salary'])
    y = data['new_salary']
    x_train, x_valid, y_train, y_valid = train_test_split(x, y, test_size=0.25,
                                                          random_state=42)
    model.fit(
        x_train,
        y_train,
        cat_features=cat_idxs,
        eval_set=(x_valid, y_valid),
        verbose=False,
        plot=False
    )

    date_version = datetime.today().strftime('%Y-%m-%d %H-%M-%S')
    path = f'{MODELS_PATH}/{profession_num}'
    if os.path.exists(path):
        model.save_model(f'{path}/{profession_num}_v{date_version}.cbm', format='cbm')
    else:
        os.mkdir(path)
        model.save_model(f'{path}/{profession_num}_v{date_version}.cbm', format='cbm')


def load_model(profession_num: int) -> CatBoostRegressor:
    path = f'{MODELS_PATH}/{profession_num}'
    models = os.listdir(path)
    model_name = models[-1]
    model = CatBoostRegressor()
    model.load_model(f'{path}/{model_name}')
    return model


def model_kwargs(model: CatBoostRegressor) -> dict:
    result = {"best_score": model.get_best_score(),
              "best_iteration": model.get_best_iteration(),
              "params": model.get_params()}
    return result


def get_learning_plot(model: CatBoostRegressor):
    learning = model.get_evals_result()
    learn = learning['learn']['RMSE']
    validation = learning['validation']['RMSE']
    plt.style.use('dark_background')
    plt.plot(range(len(learn)), learn, label='Learning RMSE', color='blue', linewidth=2, marker='o')
    plt.plot(range(len(validation)), validation, label='Validation RMSE', color='red', linewidth=2, marker='x')
    plt.title('RMSE на каждой эпохе обучения', fontsize=16)
    plt.xlabel('Эпоха', fontsize=14)
    plt.ylabel('RMSE', fontsize=14)
    plt.legend(loc='upper right', fontsize=12)
    plt.grid(True)
    plt.savefig(os.path.join('static', 'images', 'plot.png'))
    plt.close()


def get_importance_plot(profession_num: int, model: CatBoostRegressor):
    dataset = glob.glob(os.path.join(DATASETS_PATH, f'*_{profession_num}_*'))[0]
    data = pd.read_csv(dataset, index_col='id')
    data = data.drop(columns=['salary_from_rub', 'new_salary'], errors='ignore')
    importances = model.get_feature_importance(type='PredictionValuesChange')
    feature_importances = pd.Series(importances, index=data.columns).sort_values(ascending=False)

    plt.style.use('dark_background')
    bars = plt.barh(feature_importances.index[:10], feature_importances.values[:10])
    plt.bar_label(bars)
    plt.title('CatBoost Важность признаков')
    plt.xlabel('Значение важности')
    plt.ylabel('Признак')
    plt.grid(False)
    plt.savefig(os.path.join('static', 'images', 'features.png'), bbox_inches='tight')
    plt.close()


def get_list_of_professions() -> list[str]:
    with open('datasets/professions_names.json', 'r', encoding='utf-8') as f:
        return list(json.load(f).keys())


def get_list_of_models() -> list[str]:
    with open('datasets/professions_numbers.json', 'r', encoding='utf-8') as f:
        translate: dict = json.load(f)
    models = sorted(list(map(lambda x: translate[x], os.listdir(MODELS_PATH))))
    return models


def get_prof_num(name: str) -> int:
    with open('datasets/professions_names.json', 'r', encoding='utf-8') as f:
        translate = json.load(f)
    return int(translate[name])
