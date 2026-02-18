from flask import Flask, jsonify
import requests
import os
import time

app = Flask(__name__)

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
MARKET_API_KEY = os.getenv("MARKET_API_KEY")  # optional (Alpha Vantage, etc.)

# ---- cache state ----
CACHE_DURATION = 300  # 5 minutes
last_fetch_time = 0
last_index = 43


# ------------------------------------------------------------------
# NEWS SENTIMENT
# ------------------------------------------------------------------
def fetch_news_score():
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "language": "en",
        "pageSize": 20,
        "apiKey": NEWS_API_KEY,
    }

    r = requests.get(url, params=params, timeout=5)
    data = r.json()
    headlines = [a["title"].lower() for a in data.get("articles", [])]

    positive = ["growth", "peace", "win", "hope", "success", "recovery"]
    strong_negative = ["war", "attack", "death", "crisis", "disaster"]
    mild_negative = ["fear", "loss", "conflict", "tension"]

    score = 0

    for h in headlines:
        if any(w in h for w in positive):
            score += 1
        if any(w in h for w in strong_negative):
            score -= 2
        elif any(w in h for w in mild_negative):
            score -= 1

    return score


# ------------------------------------------------------------------
# MARKET SENTIMENT (very lightweight)
# ------------------------------------------------------------------
def fetch_market_score():
    """
    Uses S&P 500 daily percent change as mood proxy.
    Falls back to neutral if API unavailable.
    """

    if not MARKET_API_KEY:
        return 0  # neutral if no key configured

    try:
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": "SPY",
            "apikey": MARKET_API_KEY,
        }

        r = requests.get(url, params=params, timeout=5)
        data = r.json()

        change_pct = float(data["Global Quote"]["10. change percent"].replace("%", ""))

        # Convert percent change into small sentiment weight
        if change_pct > 1:
            return +3
        elif change_pct > 0.2:
            return +1
        elif change_pct < -1:
            return -3
        elif change_pct < -0.2:
            return -1
        else:
            return 0

    except Exception:
        return 0


# ------------------------------------------------------------------
# COMBINED EMOTION
# ------------------------------------------------------------------
def compute_emotion():
    global last_fetch_time, last_index

    now = time.time()

    # ---- serve from cache ----
    if now - last_fetch_time < CACHE_DURATION:
        return last_index

    try:
        news_score = fetch_news_score()
        market_score = fetch_market_score()

        raw_index = max(0, min(100, 45 + news_score + market_score))

        # ---- temporal smoothing ----
        smoothed = int(0.7 * last_index + 0.3 * raw_index)

        last_index = smoothed
        last_fetch_time = now

        return smoothed

    except Exception:
        return last_index


# ------------------------------------------------------------------
# ROUTES
# ------------------------------------------------------------------
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
