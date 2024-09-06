import json
import base64
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from typing import Optional, List
from datetime import datetime
from transliterate import translit
from werkzeug.datastructures import FileStorage
from sklearn.preprocessing import LabelEncoder
from sqlalchemy import Integer, Float, String, Boolean, DateTime
from sqlalchemy import Column, Table, MetaData
from sqlalchemy import create_engine, inspect
from domain import ModelFeatureImportance

MODELS_PATH = 'ml_models'
DATASETS_PATH = 'datasets'


def get_importance_plot(importances: List[ModelFeatureImportance]):
    names, values = [], []
    for elem in importances:
        names.append(elem.name)
        values.append(elem.value)

    plt.style.use('dark_background')
    plt.barh(names, values)
    plt.title('Важность признаков')
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


def get_prof_num(name: str) -> int:
    with open('datasets/professions_names.json', 'r', encoding='utf-8') as f:
        translate = json.load(f)
    return int(translate[name])


def get_prof_name(number: int) -> int:
    with open('datasets/professions_numbers.json', 'r', encoding='utf-8') as f:
        translate = json.load(f)
    return translate[str(number)]


def validate_dataset(file: FileStorage) -> (str, bool, Optional[pd.DataFrame]):
    """Валидация датасета для обучения"""
    target = 'new_salary'
    model_filters = ('is_vahta', 'experience_id', 'region_name', 'is_parttime')
    try:  # проверка, что файл вообще открывается
        data = pd.read_csv(file, index_col='id')
        data_return = data.copy()
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
            return "Данные прошли проверку!", True, data_return
        except Exception as e:
            return f"Ошибка базового преобразования данных. Ошибка: {e}", False
    except Exception as e:  # ошибка о невозможности открыть файл
        return f"Файл не считывается. Ошибка: {e}", False


def save_uploaded_dataset(dataset: pd.DataFrame, profession: int) -> str:
    """Сохранение переданного датасета (csv) в базу данных"""
    data_types = {'int64': Integer, 'float64': Float, 'bool': Boolean, 'datetime64[ns]': DateTime, 'object': String}
    columns = []
    connection_string = open('./interface_db.txt', 'r').read()
    try:
        # Создаем движок подключения
        engine = create_engine(connection_string)
        for col in dataset.columns:
            # Определяем тип данных для каждой колонки
            dtype = data_types[str(dataset[col].dtype)]
            # Переименовываем колонки с кириллическими символами в транслитерацию
            col_name = translit(col, language_code='ru', reversed=True)
            columns.append(Column(col_name, dtype))
        metadata = MetaData()
        # Создаем новую таблицу
        table_name = f"data_{profession}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        new_table = Table(table_name, metadata, *columns)
        metadata.create_all(engine)
        dataset.columns = [translit(col, language_code='ru', reversed=True) for col in dataset.columns]
        dataset.to_sql(table_name, engine, if_exists='append', index=False)
        return f"Таблица {table_name} успешно создана!"
    except Exception as e:
        return f"Ошибка при создании таблицы: {e}"


def get_all_data_tables(profession: int) -> list[str]:
    """Получение списка всех доступных слепков данных по номеру типовой профессии"""
    data_tables = f'data_{profession}'
    all_datas = inspect(create_engine(open('./interface_db.txt', 'r').read())).get_table_names()
    all_datas = [table for table in all_datas if table.startswith(data_tables)]
    return all_datas
