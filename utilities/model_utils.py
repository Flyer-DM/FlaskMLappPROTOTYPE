import os
import glob
import json
import pandas as pd
import matplotlib.pyplot as plt
from catboost import CatBoostRegressor

MODELS_PATH = 'ml_models'
DATASETS_PATH = 'datasets'


def load_model(path: str) -> CatBoostRegressor:
    model = CatBoostRegressor()
    model.load_model(path)
    return model


def model_kwargs(model: CatBoostRegressor) -> dict:
    result = {"best_score_learn": model.get_best_score()['learn']['RMSE'],
              "best_score_validation": model.get_best_score()['validation']['RMSE'],
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


def get_prof_models(number: int) -> list[str]:
    path = f'{MODELS_PATH}/{number}'
    models = os.listdir(path)
    models = list(map(lambda x: f'{path}/{x}', models))
    models.sort(key=os.path.getctime, reverse=True)
    return models


def get_prof_num(name: str) -> int:
    with open('datasets/professions_names.json', 'r', encoding='utf-8') as f:
        translate = json.load(f)
    return int(translate[name])


def get_prof_name(number: int) -> int:
    with open('datasets/professions_numbers.json', 'r', encoding='utf-8') as f:
        translate = json.load(f)
    return translate[str(number)]
