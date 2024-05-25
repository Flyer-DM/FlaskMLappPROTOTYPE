import os
import json
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from datetime import datetime


MODELS_PATH = 'ml_models'


def train_model(dataset_name: str):
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
    model.save_model(f'2_v{date_version}.cbm', format='cbm')


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


def get_list_of_models() -> list[str]:
    with open('datasets/professions_numbers.json', 'r', encoding='utf-8') as f:
        translate = json.load(f)
    models = sorted(list(map(lambda x: translate[x], os.listdir(MODELS_PATH))))
    return models


def get_prof_num(name: str) -> int:
    with open('datasets/professions_names.json', 'r', encoding='utf-8') as f:
        translate = json.load(f)
    return int(translate[name])
