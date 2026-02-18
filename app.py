from flask import Flask, jsonify

app = Flask(__name__)

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_OK = True
except Exception as e:
    VADER_OK = str(e)


@app.route("/")
def root():
    return "boot ok"


@app.route("/emotion")
def emotion():
    return jsonify({
        "vader_status": VADER_OK
    })
