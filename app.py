import os
import threading
import time
from datetime import datetime

import requests
from flask import Flask, jsonify
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

app = Flask(__name__)

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
analyzer = SentimentIntensityAnalyzer()

CURRENT_INDEX = 50.0
CURRENT_SUMMARY = "Initializing global emotional state..."
LAST_UPDATE = None

FETCH_INTERVAL = 600  # 10 minutes
FETCH_TIMEOUT = 5     # seconds


def fetch_emotion_once():
    """Fetch world emotion safely with strict timeout."""
    global CURRENT_INDEX, CURRENT_SUMMARY, LAST_UPDATE

    if not NEWS_API_KEY:
        CURRENT_SUMMARY = "Missing NEWS_API_KEY."
        return

    try:
        url = "https://newsapi.org/v2/top-headlines"
        params = {"language": "en", "pageSize": 50, "apiKey": NEWS_API_KEY}

        r = requests.get(url, params=params, timeout=FETCH_TIMEOUT)
        articles = r.json().get("articles", [])

        if not articles:
            CURRENT_SUMMARY = "No articles returned."
            return

        scores = []
        for a in articles:
            title = a.get("title", "")
            if title:
                scores.append(analyzer.polarity_scores(title)["compound"])

        if not scores:
            CURRENT_SUMMARY = "No valid headlines."
            return

        avg = sum(scores) / len(scores)
        CURRENT_INDEX = round((avg + 1) * 50, 2)

        if CURRENT_INDEX < 40:
            CURRENT_SUMMARY = "Global emotional tone is tense and negative."
        elif CURRENT_INDEX < 50:
            CURRENT_SUMMARY = "Global emotional tone is cautious and uneasy."
        elif CURRENT_INDEX < 60:
            CURRENT_SUMMARY = "Global emotional tone is mixed and watchful."
        else:
            CURRENT_SUMMARY = "Global emotional tone is hopeful and constructive."

        LAST_UPDATE = datetime.utcnow().isoformat()

    except Exception as e:
        CURRENT_SUMMARY = f"Fetch error: {str(e)}"


def background_fetch_loop():
    """Runs forever but never blocks server startup."""
    while True:
        fetch_emotion_once()
        time.sleep(FETCH_INTERVAL)


# Start background thread AFTER server boots
def start_background_thread():
    thread = threading.Thread(target=background_fetch_loop, daemon=True)
    thread.start()


@app.before_first_request
def activate_background_fetch():
    start_background_thread()


@app.route("/")
def root():
    return "Empath-Brain live."


@app.route("/emotion")
def emotion():
    return jsonify({
        "index": CURRENT_INDEX,
        "summary": CURRENT_SUMMARY,
        "last_update": LAST_UPDATE
    })


@app.route("/narrative")
def narrative():
    return jsonify({"text": CURRENT_SUMMARY})


@app.route("/witness")
def witness():
    return jsonify({"message": CURRENT_SUMMARY})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
