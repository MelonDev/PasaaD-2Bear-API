from os.path import join, dirname, realpath

import firebase_admin
import jinja2
from firebase_admin import credentials
from flask import Flask, jsonify
from src.PasaaAPI import pasaa_api
from flask_cors import CORS

from src.static.shared_database import database, marshmallow
from src.tools.DatabasePath import database_path_list
from src.tools.FileSysystemLoader import file_system_loader_list

app = Flask(__name__, template_folder='templates')
CORS(app)
app.register_blueprint(pasaa_api, url_prefix='/api')

my_loader = jinja2.ChoiceLoader([
    app.jinja_loader,
    jinja2.FileSystemLoader(file_system_loader_list),
])
app.jinja_loader = my_loader

app.debug = False
debug_database = False

app.config['SQLALCHEMY_BINDS'] = database_path_list
app.config['SQLALCHEMY_DATABASE_URI'] = database_path_list['2bear']
app.config['JSimage_generator_playground.pyON_AS_ASCII'] = True

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

app.config["UPLOAD_FOLDER"] = join(dirname(realpath(__file__)), "static/uploads")

app.config["ALLOWED_EXTENSIONS"] = ["jpg", "png", "mov", "mp4", "mpg"]
app.config["MAX_CONTENT_LENGTH"] = 1000 * 1024 * 1024  # 1000mb

database.init_app(app)
marshmallow.init_app(app)

cred = credentials.Certificate('src/fbAdminConfig.json')
firebase_admin.initialize_app(cred)


@app.route("/")
def index():
    return "PasaaD, Hello everyone!"


if __name__ == '__main__':
    app.run()
