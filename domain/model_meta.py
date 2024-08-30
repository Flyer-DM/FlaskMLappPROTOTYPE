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
    # 3 - модель обучена -> changed=1
    # 4 - скорректированы отрицательные значения -> finalized=1
    # 5 - модель финализирована
    # 6 - модель используется -> used=1
    profession = db.Column(db.Integer, nullable=True)  # Номер типовой профессии
    method = db.Column(db.Integer, db.ForeignKey("model_method.id"), nullable=True)  # Метод моделирования
    used = db.Column(db.Boolean, default=False, nullable=False)  # Используется в калькуляторе?
    retrained = db.Column(db.Integer, default=0, nullable=False)  # Сколько раз была переобучена
    orig = db.Column(db.Integer, db.ForeignKey("model_meta.id"), nullable=True)  # Ссылка на оригинал модели, если копия
    train_table = db.Column(db.String, nullable=True)  # имя таблицы для обучения
    model_file = db.Column(db.String, nullable=True)  # имя (путь) до файла модели

    author_id = db.relationship(User, foreign_keys=[author])
    last_changed_user = db.relationship(User, foreign_keys=[last_changed])
    method_id = db.relationship(ModelMethod)
    original_model = db.relationship("ModelMeta", remote_side=[id])
