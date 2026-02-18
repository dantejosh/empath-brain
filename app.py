from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def root():
    return "boot ok"

@app.route("/emotion")
def emotion():
    return jsonify({"index": 50, "summary": "boot test"})
