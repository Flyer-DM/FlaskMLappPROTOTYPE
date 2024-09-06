from flask import Flask
from domain import db


POST = "POST"
GET = "GET"


app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = open('interface_db.txt', 'r').read()
db.init_app(app)
