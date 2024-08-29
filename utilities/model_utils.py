import os
import glob
import json
import base64
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from catboost import CatBoostRegressor
from werkzeug.datastructures import FileStorage
from sklearn.preprocessing import LabelEncoder

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
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    img_bytes = base64.b64encode(buf.getvalue()).decode('utf-8')
    return img_bytes


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
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    img_bytes = base64.b64encode(buf.getvalue()).decode('utf-8')
    return img_bytes


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


def validate_dataset(file: FileStorage) -> (str, bool):
    """Валидация датасета для обучения"""
    target = 'new_salary'
    model_filters = ('is_vahta', 'experience_id', 'region_name', 'is_parttime')
    try:  # проверка, что файл вообще открывается
        data = pd.read_csv(file, index_col='id')
        columns = data.columns
        if target not in columns:  # проверка присутствия целевой переменной
            return f"Отсутствует целевая переменная \"{target}\"", False
        for column in model_filters:
            if column not in columns:  # проверка присутствия базовых признаков
                return f"Отсутствует признак \"{column}\"", False
        try:  # проверка на базовое преобразование данных
            data = data.drop(columns=['salary_from_rub', 'source_site', 'year', 'industry_group'], errors='ignore')
            columns = data.columns
            data = data.drop_duplicates(ignore_index=True)
            data_len = len(data)
            for column in columns:
                if null_sum := data[column].isnull().sum() > data_len // 2:  # проверка, что немного пустых значений
                    return f"Колонка {column} содержит слишком много пропущенных значений: {null_sum}", False
            if data_len < 10_000:  # если записей недостаточно
                return f"Данные для обучения недостаточно: {data_len}", False
            for col in data.columns[data.dtypes == object]:  # проверка на возможность преобразование данных
                data[col] = LabelEncoder().fit_transform(data[col].values)
            return "Данные прошли проверку!", True
        except Exception as e:
            return f"Ошибка базового преобразования данных. Ошибка: {e}", False
    except Exception as e:  # ошибка о тк
        return f"Файл не считывается. Ошибка: {e}", False
