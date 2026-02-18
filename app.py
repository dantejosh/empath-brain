import os
import requests
from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
MARKET_API_KEY = os.getenv("MARKET_API_KEY")  # optional (works without it)

# --------------------------------------------------
# SIMPLE KEYWORD SENTIMENT (no NLP, deterministic)
# --------------------------------------------------

POSITIVE_WORDS = [
    "growth", "gain", "peace", "deal", "recover", "record",
    "improve", "success", "optimistic", "strong"
]

NEGATIVE_WORDS = [
    "war", "crisis", "drop", "loss", "fear", "inflation",
    "conflict", "decline", "recession", "risk"
]


def headline_sentiment_score():
    """Return value in range -1 → +1"""
    try:
        url = (
            "https://newsapi.org/v2/top-headlines?"
            "language=en&pageSize=20&apiKey=" + NEWS_API_KEY
        )
        data = requests.get(url, timeout=3).json()
        articles = data.get("articles", [])

        score = 0
        count = 0

        for a in articles:
            title = (a.get("title") or "").lower()

            pos = any(w in title for w in POSITIVE_WORDS)
            neg = any(w in title for w in NEGATIVE_WORDS)

            if pos:
                score += 1
                count += 1
            elif neg:
                score -= 1
                count += 1

        if count == 0:
            return 0

        return score / count

    except Exception:
        return 0


# --------------------------------------------------
# MARKET MOOD (simple daily % change proxy)
# --------------------------------------------------

def market_sentiment_score():
    """Return value in range -1 → +1"""
    try:
        # Free demo endpoint (no key required)
        url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?interval=1d&range=2d"
        data = requests.get(url, timeout=3).json()

        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]

        if len(closes) < 2 or closes[-2] is None or closes[-1] is None:
            return 0

        change = (closes[-1] - closes[-2]) / closes[-2]

        # Clamp to reasonable emotional range
        return max(-1, min(1, change * 10))

    except Exception:
        return 0


# --------------------------------------------------
# COMBINE INTO EMOTION INDEX
# --------------------------------------------------

def compute_emotion_index():
    news = headline_sentiment_score()
    market = market_sentiment_score()

    # Weighted blend (news slightly stronger)
    combined = (0.6 * news) + (0.4 * market)

    # Map -1..1 → 0..100
    index = int(50 + combined * 25)

    # Clamp
    index = max(0, min(100, index))

    return index, news, market


def emotion_summary(index):
    if index < 30:
        return "Global emotional tone feels strained and unstable."
    elif index < 45:
        return "Global emotional tone feels tense and uncertain."
    elif index < 60:
        return "Global emotional tone feels cautious and neutral."
    elif index < 80:
        return "Global emotional tone feels steady and grounded."
    else:
        return "Global emotional tone feels optimistic and open."


# --------------------------------------------------
# ROUTES
# --------------------------------------------------

@app.route("/")
def home():
    return "Empath brain running."


@app.route("/emotion")
def emotion():
    index, news, market = compute_emotion_index()

    return jsonify({
        "index": index,
        "summary": emotion_summary(index),
        "news_component": round(news, 3),
        "market_component": round(market, 3),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


# --------------------------------------------------
# RUN
# --------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
