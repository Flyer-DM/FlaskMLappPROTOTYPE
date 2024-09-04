import numpy as np
from typing import Union
from utilities.model_utils import *
from flask_sqlalchemy.extension import SQLAlchemy
from sqlalchemy import create_engine, text
from domain import ModelMeta, ModelMethod, ModelHyperparam, ModelParam
import shap



def train_catboost(data: pd.DataFrame, profession_num: int,
                   epochs: int, early_stop: int, learning_rate: float, depth: int) -> \
                  (str, int, float, str, dict, dict):
    """Обучения модели CatBoostRegressor на переданном датасете (преобразование под модель) с входными
    гиперпараметрами (специфичными под модель); сбор и сохранение всех метрик модели; сохранение модели в виде
    файла с расширением cbm по пути в зависимости от номера типовой позиции.
    :return путь до файла модели, количество записей для обучения, rmse, mape, метрики отклонения, топ 10 признаков
    """
    target = 'new_salary'
    # удаление неиспользуемых в обучении столбцов и дубликатов
    data = data.drop(columns=['id', 'salary_from_rub', 'source_site'], errors='ignore')
    data = data.drop_duplicates()
    # подготовка категориальных признаков. TODO проверить, что есть НЕ категориальные признаки
    categorical_columns = []
    for col in data.columns[data.dtypes == object]:
        categorical_columns.append(col)
    features = [col for col in data.columns if col not in [target]]
    cat_idxs = [i for i, f in enumerate(features) if f in categorical_columns]
    # инициализация модели с переданными гиперпараметрами модели и метапараметрами
    model = CatBoostRegressor(allow_writing_files=False, iterations=epochs, loss_function='RMSE', depth=depth,
                              early_stopping_rounds=early_stop, learning_rate=learning_rate, thread_count=-1,
                              eval_metric='MAPE')
    # отбор данных для обучения
    x = data.drop(columns=['new_salary'])
    y = data['new_salary']
    # запуск обучения модели
    model.fit(
        x,
        y,
        cat_features=cat_idxs,
        verbose=False,
        plot=False
    )
    # сбор метрик модели
    n = data.shape[0]
    rmse = model.get_best_score()['learn']['RMSE']
    mape = f"{model.get_best_score()['learn']['MAPE'] * 100:.2f}%"
    dev_metrics = deviation_metric(y, model.predict(x))
    # топ 10 важнейших признаков
    x.columns = [translit(col, 'ru') for col in x.columns]
    importances = model.get_feature_importance(type='PredictionValuesChange')
    feature_importances = pd.Series(importances, index=x.columns).sort_values(ascending=False)[:10].to_dict()
    # сохранение файла модели по дате/времени обучения в директорию с номером ТП
    date_version = datetime.now().strftime('%Y%m%d%H%M%S')
    path = f'{MODELS_PATH}/{profession_num}'
    if os.path.exists(path):
        model.save_model(filename := f'{path}/{profession_num}_v{date_version}.cbm', format='cbm')
    else:
        os.mkdir(path)
        model.save_model(filename := f'{path}/{profession_num}_v{date_version}.cbm', format='cbm')
    return 'filename', n, rmse, mape, dev_metrics, feature_importances


def train_model(model_id: int) -> (str, int, float, str, dict, dict):
    """Запуск обучения модели по номеру id модели с отбором данных через WHERE"""
    engine = create_engine(open('./interface_db.txt', 'r').read())
    model: ModelMeta = ModelMeta.query.get(model_id)
    param: ModelParam = ModelParam.query.filter_by(model_id=model_id).first()
    query = text(f"SELECT * FROM {model.train_table} WHERE is_vahta = '{param.is_vahta}' AND "
                 f"is_parttime = '{param.is_parttime}' AND experience_id = '{param.experience_id}' AND "
                 f"region_name = '{param.region_name}'")
    with engine.connect() as connection:
        result = connection.execute(query)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())

    model_name = ModelMethod.query.filter_by(id=model.method).first().name

    if model_name == 'CatBoostRegressor':
        return train_catboost(
            df, model.profession,
            int(ModelHyperparam.query.filter_by(model_id=model_id, name='epochs').first().value),
            int(ModelHyperparam.query.filter_by(model_id=model_id, name='early_stop').first().value),
            float(ModelHyperparam.query.filter_by(model_id=model_id, name='learning_rate').first().value),
            int(ModelHyperparam.query.filter_by(model_id=model_id, name='depth').first().value)
        )
    elif model_name == 'LinearRegression':
        return train_linear_regression(
            df, model.profession
        )


def add_model_hyperparams(db: SQLAlchemy, model_id: str, *params) -> None:
    for param_name, param_value in params:
        if hyperparam := ModelHyperparam.query.filter_by(model_id=model_id, name=param_name).first():
            hyperparam.value = param_value
        else:
            db.session.add(ModelHyperparam(model_id=model_id, name=param_name, value=param_value))


def get_catboost_hyperparams(model_id: Union[int, str]) -> dict:
    epochs = ModelHyperparam.query.filter_by(model_id=model_id, name='epochs').first().value
    early_stop = ModelHyperparam.query.filter_by(model_id=model_id, name='early_stop').first().value
    learning_rate = ModelHyperparam.query.filter_by(model_id=model_id, name='learning_rate').first().value
    depth = ModelHyperparam.query.filter_by(model_id=model_id, name='depth').first().value
    return {
        'epochs': epochs,
        'early_stop': early_stop,
        'learning_rate': learning_rate,
        'depth': depth,
    }


def deviation_metric(true_values: pd.Series, pred_values: np.ndarray):
    """Получение метрик: сколько процентов предсказанных значений от всех имеющихся отклоняются более/не более чем
    на n процентов от истинного значения.
    :arg true_values - истинные значения.
    :arg pred_values - предсказанные моделью значения.
    """
    metric_x = {}  # процент отклонений от реального значения МЕНЕЕ чем на [1, 3, 5, 10, 15, 20, 25] включительно
    metric_y = {}  # процент отклонений от реального значения БОЛЕЕ чем на (200, 150, 100, 75, 50, 25) не включительно

    true_values = np.array(true_values)
    deviation = abs(true_values - pred_values) / true_values * 100  # проценты отклонений всех значений

    for percent in (1, 3, 5, 10, 15, 20, 25):
        dev = deviation <= percent
        metric_x[f'less_{percent}'] = f'{sum(dev) / len(dev) * 100:.2f}%'
    for percent in [200, 150, 100, 75, 50, 25]:
        dev = deviation > percent
        metric_y[f'more_{percent}'] = f'{sum(dev) / len(dev) * 100:.2f}%'
    return {**metric_x, **metric_y}


def train_linear_regression(data: pd.DataFrame, profession_num: int) -> str:
    target = 'new_salary'

    data = data.drop(columns=['id', 'salary_from_rub', 'source_site'], errors='ignore')

    categorical_features = data.select_dtypes(include=['object']).columns
    label_encoders = {}

    for feature in categorical_features:
        le = LabelEncoder()
        data[feature] = le.fit_transform(data[feature])
        label_encoders[feature] = le

    features = [col for col in data.columns if col not in [target]]

    x = data[features]
    y = data[target]

    x_train, x_valid, y_train, y_valid = train_test_split(x, y, random_state=42)

    model = LinearRegression()
    model.fit(x_train, y_train)

    y_pred = model.predict(x_valid)
    mse = mean_squared_error(y_valid, y_pred)
    print(f"Mean Squared Error: {mse}")

    explainer = shap.Explainer(model, x_train)
    shap_values = explainer(x_valid)
    feature_importance = np.abs(shap_values.values).mean(axis=0)
    feature_importance_df = pd.DataFrame({
        "feature": shap_values.feature_names,
        "importance": feature_importance
    })
    top_10_features = feature_importance_df.sort_values(by="importance", ascending=False).head(10)
    for index, row in top_10_features.iterrows():
        print(f"Признак: {row['feature']}, Важность: {row['importance']:.4f}")


    date_version = datetime.now().strftime('%Y%m%d%H%M%S')
    path = f'{MODELS_PATH}/{profession_num}'
    filename = f'{path}/{profession_num}_v{date_version}.pkl'

    if not os.path.exists(path):
        os.makedirs(path)

    with open(filename, 'wb') as f:
        pickle.dump(model, f)

    return filename
