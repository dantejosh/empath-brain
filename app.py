import os
import threading
import time
from datetime import datetime

import requests
from flask import Flask, jsonify

app = Flask(__name__)

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

CURRENT_INDEX = 50.0
CURRENT_SUMMARY = "Initializing global emotional state..."
LAST_UPDATE = None

updater_started = False


NEGATIVE = [
    "war","attack","killed","death","crisis","disaster","explosion",
    "conflict","strike","collapse","flood","earthquake","shooting",
    "threat","sanctions"
]

POSITIVE = [
    "peace","agreement","growth","recovery","aid","rescue","ceasefire",
    "progress","breakthrough","expansion","stability"
]


def score(text: str) -> int:
    t = text.lower()
    neg = sum(w in t for w in NEGATIVE)
    pos = sum(w in t for w in POSITIVE)

    if pos > neg:
        return 1
    if neg > pos:
        return -1
    return 0


def compute_emotion():
    if not NEWS_API_KEY:
        raise Exception("Missing NEWS_API_KEY")

    url = "https://newsapi.org/v2/top-headlines"
    params = {"language": "en", "pageSize": 50, "apiKey": NEWS_API_KEY}

    r = requests.get(url, params=params, timeout=10)
    data = r.json()
    articles = data.get("articles", [])

    if not articles:
        raise Exception("No articles returned")

    scores = [score(a.get("title", "")) for a in articles]
    avg = sum(scores) / len(scores)

    index = round((avg + 1) * 50, 2)

    if index < 40:
        summary = "Global emotional tone is tense and unstable."
    elif index < 50:
        summary = "Global emotional tone is cautious and uncertain."
    elif index < 60:
        summary = "Global emotional tone is mixed but stabilizing."
    else:
        summary = "Global emotional tone is hopeful and constructive."

    return index, summary


def updater_loop():
    global CURRENT_INDEX, CURRENT_SUMMARY, LAST_UPDATE

    while True:
        try:
            idx, summ = compute_emotion()
            CURRENT_INDEX = idx
            CURRENT_SUMMARY = summ
            LAST_UPDATE = datetime.utcnow().isoformat()
            print(f"[UPDATE] {LAST_UPDATE} → {idx}")
        except Exception as e:
            print("Update error:", e)

        time.sleep(1800)  # 30 minutes


@app.before_request
def start_updater_once():
    """
    Start background updater only after server is live.
    Prevents Render deploy hang.
    """
    global updater_started
    if not updater_started:
        threading.Thread(target=updater_loop, daemon=True).start()
        updater_started = True
        print("[START] Background updater launched")


@app.route("/")
def root():
    return "Empath-Brain live."


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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
