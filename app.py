from flask import Flask, jsonify, render_template_string
import datetime
import os
import requests

app = Flask(__name__)

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------

NEWS_API_KEY = os.getenv("NEWS_API_KEY")  # set in Render dashboard
SP500_URL = "https://query1.finance.yahoo.com/v7/finance/quote?symbols=%5EGSPC"


# -------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------

POSITIVE_WORDS = {
    "growth", "gain", "recovery", "progress", "peace",
    "stability", "innovation", "agreement", "support", "improve"
}

NEGATIVE_WORDS = {
    "war", "conflict", "crisis", "decline", "loss",
    "fear", "violence", "collapse", "threat", "recession"
}


def simple_sentiment_score(text):
    """Very lightweight, deterministic sentiment scoring."""
    if not text:
        return 0

    words = text.lower().split()
    score = 0

    for w in words:
        if w in POSITIVE_WORDS:
            score += 1
        if w in NEGATIVE_WORDS:
            score -= 1

    return score


# -------------------------------------------------------------------
# NEWS SENTIMENT
# -------------------------------------------------------------------

def fetch_news_score():
    if not NEWS_API_KEY:
        return 0

    try:
        url = (
            "https://newsapi.org/v2/top-headlines?"
            "language=en&pageSize=20&apiKey=" + NEWS_API_KEY
        )
        r = requests.get(url, timeout=5)
        data = r.json()

        articles = data.get("articles", [])

        total = 0
        for a in articles:
            text = (a.get("title") or "") + " " + (a.get("description") or "")
            total += simple_sentiment_score(text)

        return total

    except Exception:
        return 0


# -------------------------------------------------------------------
# MARKET SENTIMENT
# -------------------------------------------------------------------

def fetch_market_score():
    try:
        r = requests.get(SP500_URL, timeout=5)
        data = r.json()

        quote = data["quoteResponse"]["result"][0]

        change_percent = quote.get("regularMarketChangePercent", 0)

        # scale roughly into sentiment band
        return change_percent / 2.0

    except Exception:
        return 0


# -------------------------------------------------------------------
# EMOTION ENGINE
# -------------------------------------------------------------------

def compute_emotion():
    """
    Combine news + market into stable 0–100 index.
    """

    news = fetch_news_score()
    market = fetch_market_score()

    # weighted blend
    raw = 50 + news * 2 + market * 5

    # clamp
    index = max(0, min(100, int(raw)))

    # summary bands
    if index < 30:
        summary = "Global tone feels strained and unsettled."
    elif index < 45:
        summary = "Global tone feels tense and uncertain."
    elif index < 60:
        summary = "Global tone feels cautious and steady."
    elif index < 80:
        summary = "Global tone feels grounded and calm."
    else:
        summary = "Global tone feels open and optimistic."

    return index, summary, news, market


# -------------------------------------------------------------------
# JSON ENDPOINT FOR ESP32
# -------------------------------------------------------------------

@app.route("/emotion")
def emotion():
    index, summary, news, market = compute_emotion()

    return jsonify({
        "index": index,
        "summary": summary,
        "news_component": round(news, 2),
        "market_component": round(market, 2),
        "timestamp": datetime.datetime.utcnow().isoformat()
    })


# -------------------------------------------------------------------
# QUIET MUSEUM WITNESS PAGE
# -------------------------------------------------------------------

WITNESS_TEMPLATE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Global Emotion Witness</title>
<style>
body {
    margin: 0;
    background: #0b0b0b;
    color: #e8e6e3;
    font-family: Georgia, "Times New Roman", serif;
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100vh;
}
.container {
    max-width: 520px;
    text-align: center;
    line-height: 1.6;
}
.index {
    font-size: 64px;
    margin-bottom: 24px;
}
.summary {
    font-size: 20px;
    opacity: 0.9;
    margin-bottom: 32px;
}
.meta {
    font-size: 13px;
    opacity: 0.5;
}
</style>
</head>
<body>
<div class="container">
    <div class="index">{{ index }}</div>
    <div class="summary">{{ summary }}</div>
    <div class="meta">
        News influence: {{ news }} |
        Market influence: {{ market }}<br>
        Observed {{ timestamp }} UTC
    </div>
</div>
</body>
</html>
"""


@app.route("/witness")
def witness():
    index, summary, news, market = compute_emotion()
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")

    return render_template_string(
        WITNESS_TEMPLATE,
        index=index,
        summary=summary,
        news=round(news, 2),
        market=round(market, 2),
        timestamp=timestamp
    )


# -------------------------------------------------------------------
# ROOT
# -------------------------------------------------------------------

@app.route("/")
def home():
    return "Global Emotion Service Running"


# -------------------------------------------------------------------
# ENTRY
# -------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
