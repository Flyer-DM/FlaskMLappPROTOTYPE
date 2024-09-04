# import threading
from utilities.model_utils import *
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from datetime import datetime
from flask_sqlalchemy.extension import SQLAlchemy
from sqlalchemy import create_engine, text
from domain import ModelMeta, ModelMethod, ModelHyperparam, ModelParam


def train_catboost(data: pd.DataFrame, profession_num: int,
                   epochs: int, early_stop: int, train_test: float, learning_rate: float, depth: int) -> str:
    target = 'new_salary'

    data = data.drop(columns=['id', 'salary_from_rub', 'source_site'], errors='ignore')

    categorical_columns = []
    for col in data.columns[data.dtypes == object]:
        data[col] = LabelEncoder().fit_transform(data[col].values)
        categorical_columns.append(col)
    features = [col for col in data.columns if col not in [target]]
    cat_idxs = [i for i, f in enumerate(features) if f in categorical_columns]

    model = CatBoostRegressor(allow_writing_files=False, iterations=epochs, loss_function='RMSE', depth=depth,
                              early_stopping_rounds=early_stop, learning_rate=learning_rate)

    x = data.drop(columns=['new_salary'])
    y = data['new_salary']
    x_train, x_valid, y_train, y_valid = train_test_split(x, y, test_size=train_test,
                                                          random_state=42)
    model.fit(
        x_train,
        y_train,
        cat_features=cat_idxs,
        eval_set=(x_valid, y_valid),
        verbose=False,
        plot=False
    )

    date_version = datetime.now().strftime('%Y%m%d%H%M%S')
    path = f'{MODELS_PATH}/{profession_num}'
    if os.path.exists(path):
        model.save_model(filename := f'{path}/{profession_num}_v{date_version}.cbm', format='cbm')
    else:
        os.mkdir(path)
        model.save_model(filename := f'{path}/{profession_num}_v{date_version}.cbm', format='cbm')
    return filename


def train_model(model_id: int) -> str:
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
            float(ModelHyperparam.query.filter_by(model_id=model_id, name='train_test').first().value),
            float(ModelHyperparam.query.filter_by(model_id=model_id, name='learning_rate').first().value),
            int(ModelHyperparam.query.filter_by(model_id=model_id, name='depth').first().value)
        )
    elif model_name == 'LinearRegression':
        return train_linear_regression(
            df, model.profession
        )


# def train_model_assync(model_id: int):
#     thread = threading.Thread(target=train_model, args=(model_id, ))
#     thread.start()


def add_model_hyperparams(db: SQLAlchemy, model_id: int, *params) -> None:
    for param_name, param_value in params:
        if hyperparam := ModelHyperparam.query.filter_by(model_id=model_id, name=param_name).first():
            hyperparam.value = param_value
        else:
            db.session.add(ModelHyperparam(model_id=model_id, name=param_name, value=param_value))


def get_catboost_hyperparams(model_id: int) -> dict:
    epochs = ModelHyperparam.query.filter_by(model_id=model_id, name='epochs').first().value
    early_stop = ModelHyperparam.query.filter_by(model_id=model_id, name='early_stop').first().value
    train_test = ModelHyperparam.query.filter_by(model_id=model_id, name='train_test').first().value
    learning_rate = ModelHyperparam.query.filter_by(model_id=model_id, name='learning_rate').first().value
    depth = ModelHyperparam.query.filter_by(model_id=model_id, name='depth').first().value
    return {
        'epochs': epochs,
        'early_stop': early_stop,
        'train_test': train_test,
        'learning_rate': learning_rate,
        'depth': depth,
    }

# def get_linear_regression_hyperparams(model_id: int) -> dict:
#     train_test = ModelHyperparam.query.filter_by(model_id=model_id, name='train_test').first().value
#     return {
#         'train_test': train_test
#     }


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

    date_version = datetime.now().strftime('%Y%m%d%H%M%S')
    path = f'{MODELS_PATH}/{profession_num}'
    filename = f'{path}/{profession_num}_v{date_version}.pkl'
    
    if not os.path.exists(path):
        os.makedirs(path)

    with open(filename, 'wb') as f:
        pickle.dump(model, f)
    
    return filename
