import os

from werkzeug.utils import secure_filename
from flask import Flask, jsonify, send_from_directory, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

from .models.base import db
from .models.Settings import Settings
from .models.Players import Players
from .models.Rosters import Rosters

# from config import Config

app = Flask(__name__)

# Establish config variables
# config = Config()
# app.config.from_object(config)
# print("DB_URI: ", app.config["SQLALCHEMY_DATABASE_URI"])
# db.init_app(app)


@app.route("/")
def hello_world():
    return jsonify(hello="world")


@app.route("/static/<path:filename>")
def staticfiles(filename):
    return send_from_directory(app.config["STATIC_FOLDER"], filename)


@app.route("/media/<path:filename>")
def mediafiles(filename):
    return send_from_directory(app.config["MEDIA_FOLDER"], filename)


@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files["file"]
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config["MEDIA_FOLDER"], filename))

    return """
    <!doctype html>
    <title>upload new File</title>
    <form action="" method=post enctype=multipart/form-data>
        <p><input type=file name=file><input type=submit value=Upload>
    </form>
    """


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
