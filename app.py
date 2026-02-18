import os
import requests
from flask import Flask, jsonify

app = Flask(__name__)

# Read environment variable correctly
NEWS_API_KEY = os.getenv("NEWS_API_KEY")


@app.route("/")
def home():
    return "Empath-Brain debug server running."


@app.route("/emotion")
def emotion():
    """
    TEMP DEBUG ROUTE
    Shows exactly what NewsAPI returns from inside Render.
    """

    if not NEWS_API_KEY:
        return jsonify({
            "error": "NEWS_API_KEY not found in environment",
            "env_key_present": False
        })

    try:
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "language": "en",
            "pageSize": 5,
            "apiKey": NEWS_API_KEY
        }

        r = requests.get(url, params=params, timeout=10)

        return jsonify({
            "env_key_present": True,
            "status_code": r.status_code,
            "response_json": r.json()
        })

    except Exception as e:
        return jsonify({
            "env_key_present": True,
            "exception": str(e)
        })


@app.route("/narrative")
def narrative():
    return "Debug mode active."


@app.route("/witness")
def witness():
    return "Debug mode active."


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
