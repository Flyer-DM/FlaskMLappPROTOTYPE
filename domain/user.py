from domain.db_connection import db
from werkzeug.security import check_password_hash
from flask_login import UserMixin


class User(UserMixin, db.Model):
    __tablename__ = 'interface_user'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)

    def check_password(self, password):
        return check_password_hash(self.password, password)
