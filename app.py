from flask import Flask, jsonify, Response
import requests
import statistics
import threading
import time
from datetime import datetime

app = Flask(__name__)

# ---------- Global emotional state ----------

CURRENT_INDEX = 50.0
CURRENT_SUMMARY = "Initializing global emotional state..."
LAST_UPDATE = None


# ---------- Data Sources ----------

def get_market_sentiment():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?range=1d&interval=5m"
        r = requests.get(url, timeout=10)
        data = r.json()

        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        closes = [c for c in closes if c is not None]

        if len(closes) < 2:
            return 50.0

        change_pct = ((closes[-1] - closes[0]) / closes[0]) * 100
        index = max(0, min(100, 50 + (change_pct * 25)))

        return round(index, 2)

    except Exception:
        return 50.0


def get_news_sentiment():
    try:
        url = "https://hnrss.org/frontpage.jsonfeed"
        r = requests.get(url, timeout=10)
        items = r.json().get("items", [])[:20]

        lengths = [len(item.get("title", "")) for item in items]
        if not lengths:
            return 50.0

        volatility = statistics.pstdev(lengths)
        index = max(0, min(100, 50 + (volatility - 20)))

        return round(index, 2)

    except Exception:
        return 50.0


# ---------- Emotion Engine ----------

def build_summary(index, market, news):
    if index < 35:
        tone = "heavy and pessimistic"
    elif index < 45:
        tone = "cautious and uncertain"
    elif index < 60:
        tone = "balanced with mixed signals"
    elif index < 75:
        tone = "guardedly optimistic"
    else:
        tone = "strongly positive and confident"

    return (
        f"Global emotional tone is {tone}. "
        f"Market signal: {market:.1f}. "
        f"News tension signal: {news:.1f}."
    )


def compute_global_emotion():
    market = get_market_sentiment()
    news = get_news_sentiment()

    blended = (market * 0.6) + (news * 0.4)
    summary = build_summary(blended, market, news)

    return round(blended, 2), summary


# ---------- Background updater ----------

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

        # update every hour
        time.sleep(3600)


# Start background thread once
threading.Thread(target=emotion_updater, daemon=True).start()


# ---------- Routes ----------

@app.route("/")
def root():
    return "Empath-Brain is running."


@app.route("/emotion")
def emotion():
    return jsonify({
        "index": CURRENT_INDEX,
        "summary": CURRENT_SUMMARY,
        "last_update": LAST_UPDATE
    })


@app.route("/narrative")
def narrative():
    return jsonify({
        "index": CURRENT_INDEX,
        "summary": CURRENT_SUMMARY,
        "last_update": LAST_UPDATE
    })


@app.route("/witness")
def witness():
    html = f"""
    <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <style>
                body {{
                    margin: 0;
                    background: black;
                    color: white;
                    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    height: 100vh;
                    text-align: center;
                    padding: 40px;
                    font-size: 22px;
                    line-height: 1.5;
                }}
                .meta {{
                    margin-top: 20px;
                    font-size: 16px;
                    opacity: 0.6;
                }}
            </style>
        </head>
        <body>
            <div>
                {CURRENT_SUMMARY}
                <div class="meta">
                    Index: {CURRENT_INDEX}<br/>
                    Updated: {LAST_UPDATE}
                </div>
            </div>
        </body>
    </html>
    """

    return Response(html, mimetype="text/html")


# ---------- Run ----------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
