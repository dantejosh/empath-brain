import threading
import time
from datetime import datetime
import os
import requests

from flask import Flask, jsonify

app = Flask(__name__)

# ---------- CONFIG ----------
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# ---------- GLOBAL STATE ----------
CURRENT_INDEX = 50.0
CURRENT_SUMMARY = "Initializing global emotional state..."
LAST_UPDATE = None


# ---------- SENTIMENT HELPERS ----------
NEGATIVE_WORDS = [
    "war", "attack", "killed", "death", "crisis", "disaster",
    "explosion", "conflict", "strike", "collapse", "flood",
    "earthquake", "shooting", "threat", "sanctions"
]

POSITIVE_WORDS = [
    "peace", "agreement", "growth", "recovery", "aid",
    "rescue", "ceasefire", "progress", "breakthrough",
    "expansion", "stability"
]


def score_headline(text: str) -> int:
    """Return sentiment score from -1 to +1."""
    t = text.lower()

    neg = sum(word in t for word in NEGATIVE_WORDS)
    pos = sum(word in t for word in POSITIVE_WORDS)

    if pos > neg:
        return 1
    if neg > pos:
        return -1
    return 0


# ---------- REAL EMOTION ENGINE ----------
def compute_global_emotion():
    if not NEWS_API_KEY:
        raise Exception("Missing NEWS_API_KEY")

    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "language": "en",
        "pageSize": 50,
        "apiKey": NEWS_API_KEY
    }

    r = requests.get(url, params=params, timeout=10)
    data = r.json()

    articles = data.get("articles", [])

    if not articles:
        raise Exception("No news articles returned")

    scores = []

    for a in articles:
        title = a.get("title") or ""
        scores.append(score_headline(title))

    avg = sum(scores) / len(scores)

    # convert -1..1 → 0..100
    index = round((avg + 1) * 50, 2)

    # narrative
    if index < 40:
        summary = "Global emotional tone is tense and unstable."
    elif index < 50:
        summary = "Global emotional tone is cautious and uncertain."
    elif index < 60:
        summary = "Global emotional tone is mixed but stabilizing."
    else:
        summary = "Global emotional tone is hopeful and constructive."

    return index, summary


# ---------- BACKGROUND LOOP ----------
def emotion_updater():
    global CURRENT_INDEX, CURRENT_SUMMARY, LAST_UPDATE

    while True:
        try:
            index, summary = compute_global_emotion()

            CURRENT_INDEX = index
            CURRENT_SUMMARY = summary
            LAST_UPDATE = datetime.utcnow().isoformat()

            print(f"[UPDATE] {LAST_UPDATE} → {index}")

        except Exception as e:
            print("Update error:", e)

        # update every 30 minutes
        time.sleep(1800)


# ---------- INITIAL RUN ----------
def initialize_emotion():
    global CURRENT_INDEX, CURRENT_SUMMARY, LAST_UPDATE

    try:
        index, summary = compute_global_emotion()
        CURRENT_INDEX = index
        CURRENT_SUMMARY = summary
        LAST_UPDATE = datetime.utcnow().isoformat()
        print(f"[INIT] {LAST_UPDATE} → {index}")
    except Exception as e:
        print("Initialization error:", e)


initialize_emotion()
threading.Thread(target=emotion_updater, daemon=True).start()


# ---------- ROUTES ----------
@app.route("/")
def home():
    return "Empath-Brain is running."


@app.route("/emotion")
def emotion():
    return jsonify({
        "index": CURRENT_INDEX,
        "last_update": LAST_UPDATE,
        "summary": CURRENT_SUMMARY
    })


@app.route("/narrative")
def narrative():
    return jsonify({"text": CURRENT_SUMMARY})


@app.route("/witness")
def witness():
    return jsonify({"message": CURRENT_SUMMARY})


# ---------- RUN ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

