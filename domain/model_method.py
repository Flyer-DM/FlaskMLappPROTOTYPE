from domain.db_connection import db


class ModelMethod(db.Model):
    __tablename__ = 'model_method'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)  # Название метода моделирования
