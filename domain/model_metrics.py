from domain.db_connection import db
from domain.model_meta import ModelMeta


class ModelMetrics(db.Model):
    __tablename__ = 'model_metrics'

    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey("model_meta.id"), nullable=False)
    n = db.Column(db.Integer, nullable=False)
    rmse = db.Column(db.Integer, nullable=False)
    mape = db.Column(db.String, nullable=False)
    less_1 = db.Column(db.String, nullable=False)
    less_3 = db.Column(db.String, nullable=False)
    less_5 = db.Column(db.String, nullable=False)
    less_10 = db.Column(db.String, nullable=False)
    less_15 = db.Column(db.String, nullable=False)
    less_20 = db.Column(db.String, nullable=False)
    less_25 = db.Column(db.String, nullable=False)
    more_200 = db.Column(db.String, nullable=False)
    more_150 = db.Column(db.String, nullable=False)
    more_100 = db.Column(db.String, nullable=False)
    more_75 = db.Column(db.String, nullable=False)
    more_50 = db.Column(db.String, nullable=False)
    more_25 = db.Column(db.String, nullable=False)
    # прямые ссылки
    model = db.relationship(ModelMeta, foreign_keys=[model_id])
    # обратные ссылки
    metrics = db.relationship('ModelFeatureImportance', backref='model_metrics', cascade='all, delete-orphan')
