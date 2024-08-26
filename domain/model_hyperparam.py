from domain.db_connection import db


class ModelHyperparam(db.Base):
    __tablename__ = 'model_hyperparam'

    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey("model_meta.id"), nullable=False)
    name = db.Column(db.String, nullable=False)  # Название гиперпараметра модели
    value = db.Column(db.String, nullable=False)  # Значение гиперпараметра модели
