from utilities.model_utils import *
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from datetime import datetime
from werkzeug.datastructures import FileStorage


def train_catboost(dataset_name: FileStorage, profession_num: int,
                   epochs: int, early_stop: int, train_test: float, learning_rate: float, depth: int):
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
        model.save_model(f'{path}/{profession_num}_v{date_version}.cbm', format='cbm')
    else:
        os.mkdir(path)
        model.save_model(f'{path}/{profession_num}_v{date_version}.cbm', format='cbm')