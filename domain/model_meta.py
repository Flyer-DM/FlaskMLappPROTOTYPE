from datetime import datetime
from domain.db_connection import db
from domain.user import User
from domain.model_method import ModelMethod


class ModelMeta(db.Model):
    __tablename__ = 'model_meta'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)  # Название модели
    author = db.Column(db.Integer, db.ForeignKey("interface_user.id"), nullable=False)  # Автор модели
    description = db.Column(db.String, nullable=True)  # Описание
    creation_on = db.Column(db.DateTime, default=datetime.now, nullable=False)  # Время создания
    last_changed = db.Column(db.Integer, db.ForeignKey("interface_user.id"), nullable=False)  # Пользователь, изменивший
    # модель последний раз
    updated_on = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)  # Время, когда
    # последний раз модель была изменена пользователем
    finalized = db.Column(db.Boolean, default=False, nullable=False)  # Модель финализирована?
    state = db.Column(db.Integer, default=0, nullable=False)  # Состояние модели:
    # 0 - создана запись о модели в БД (автор/дата/описание/типовая позиция)
    # 1 - выбран метод моделирования
    # 2 - выбраны гиперпараметры метода моделирования
    # 3 - выбран слепок данных для модели
    # 4 - выбраны фильтры для модели (параметры)
    # 5 - модель обучена -> retrained=1
    # 6 - скорректированы отрицательные значения
    # 7 - модель финализирована -> finalized=1
    # 8 - модель используется -> used=1
    profession = db.Column(db.Integer, nullable=True)  # Номер типовой профессии
    method = db.Column(db.Integer, db.ForeignKey("model_method.id"), nullable=True)  # Метод моделирования
    used = db.Column(db.Boolean, default=False, nullable=False)  # Используется в калькуляторе?
    retrained = db.Column(db.Integer, default=0, nullable=False)  # Сколько раз была переобучена
    orig = db.Column(db.Integer, db.ForeignKey("model_meta.id", ondelete='SET NULL'), nullable=True)  # Оригинал
    train_table = db.Column(db.String, nullable=True)  # имя таблицы для обучения
    model_file = db.Column(db.String, nullable=True)  # имя (путь) до файла модели
    # прямые ссылки
    author_id = db.relationship(User, foreign_keys=[author])
    last_changed_user = db.relationship(User, foreign_keys=[last_changed])
    method_id = db.relationship(ModelMethod)
    # обратные ссылки
    original_model = db.relationship('ModelMeta', remote_side=[id], backref='children')
    hyperparams = db.relationship('ModelHyperparam', backref='model_meta', cascade='all, delete-orphan')
    params = db.relationship('ModelParam', backref='model_meta', cascade='all, delete-orphan')
    metrics = db.relationship('ModelMetrics', backref='model_meta', cascade='all, delete-orphan')
