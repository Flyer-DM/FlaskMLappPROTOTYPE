from domain.db_connection import db
from domain.model_metrics import ModelMetrics


class ModelFeatureImportance(db.Model):
    __tablename__ = 'model_feature_importance'

    id = db.Column(db.Integer, primary_key=True)
    model_metrics_id = db.Column(db.Integer, db.ForeignKey("model_metrics.id"), nullable=False)
    top = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String, nullable=False)
    value = db.Column(db.Float, nullable=False)
    # прямые ссылки
    metrics = db.relationship(ModelMetrics, foreign_keys=[model_metrics_id])
