from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def index():
    return "PasaaD, Hello everyone!"

if __name__ == '__main__':
    app.run()
