from domain.db_connection import db
from domain.model_meta import ModelMeta


class ModelParam(db.Model):
    __tablename__ = 'model_param'

    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey("model_meta.id"), nullable=False)
    is_vahta = db.Column(db.Boolean, nullable=False)
    is_parttime = db.Column(db.Boolean, nullable=False)
    experience_id = db.Column(db.Integer, nullable=False)
    region_name = db.Column(db.String, nullable=False)
    # прямые ссылки
    model = db.relationship(ModelMeta, foreign_keys=[model_id])
