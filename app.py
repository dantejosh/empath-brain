from flask import Flask, jsonify
import requests
import os
import time

app = Flask(__name__)

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# ---- simple in-memory state (safe on Render) ----
CACHE_DURATION = 300  # 5 minutes
last_fetch_time = 0
last_index = 43  # stable non-50 starting point


def fetch_raw_emotion():
    """Pull headlines and compute weighted keyword score."""
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "language": "en",
        "pageSize": 20,
        "apiKey": NEWS_API_KEY,
    }

    r = requests.get(url, params=params, timeout=5)
    data = r.json()
    headlines = [a["title"].lower() for a in data.get("articles", [])]

    positive_words = ["growth", "peace", "win", "hope", "success", "recover", "recovery"]
    strong_negative = ["war", "attack", "death", "crisis", "disaster"]
    mild_negative = ["fear", "loss", "conflict", "tension"]

    score = 0

    for h in headlines:
        if any(w in h for w in positive_words):
            score += 1
        if any(w in h for w in strong_negative):
            score -= 2
        elif any(w in h for w in mild_negative):
            score -= 1

    # Center near mid-40s
    raw_index = max(0, min(100, 45 + score))
    return raw_index


def compute_emotion():
    """
    Cached + smoothed emotion computation.
    Still fully synchronous and safe.
    """
    global last_fetch_time, last_index

    now = time.time()

    # Use cache if within 5 minutes
    if now - last_fetch_time < CACHE_DURATION:
        return last_index

    try:
        raw_index = fetch_raw_emotion()

        # ---- temporal smoothing ----
        smoothed = int(0.7 * last_index + 0.3 * raw_index)

        last_index = smoothed
        last_fetch_time = now

        return smoothed

    except Exception:
        # fallback keeps sculpture alive
        return last_index


@app.route("/emotion")
def emotion():
    index = compute_emotion()

    if index < 40:
        summary = "Global emotional tone is tense and uncertain."
    elif index < 60:
        summary = "Global emotional tone is cautious and uncertain."
    else:
        summary = "Global emotional tone is stable with cautious optimism."

    return jsonify({
        "index": index,
        "summary": summary
    })


@app.route("/")
def home():
    return "Emotion server running."
