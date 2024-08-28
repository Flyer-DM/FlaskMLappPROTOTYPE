from domain.db_connection import db
from domain.model_meta import ModelMeta


class ModelHyperparam(db.Model):
    __tablename__ = 'model_hyperparam'

    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey("model_meta.id"), nullable=False)
    name = db.Column(db.String, nullable=False)  # Название гиперпараметра модели
    value = db.Column(db.String, nullable=False)  # Значение гиперпараметра модели

    model = db.relationship(ModelMeta, foreign_keys=[model_id])
