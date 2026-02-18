from flask import Flask, jsonify, Response
import requests
import statistics
import time

app = Flask(__name__)

# ---------- Helpers ----------

def get_market_sentiment():
    """
    Pull recent S&P 500 data from Yahoo Finance.
    Convert % daily change into 0–100 emotion scale.
    """
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EGSPC?range=1d&interval=5m"
        r = requests.get(url, timeout=10)
        data = r.json()

        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        closes = [c for c in closes if c is not None]

        if len(closes) < 2:
            return 50.0

        change_pct = ((closes[-1] - closes[0]) / closes[0]) * 100

        # Map −2% → 0, 0% → 50, +2% → 100 (clamped)
        index = max(0, min(100, 50 + (change_pct * 25)))
        return round(index, 2)

    except Exception:
        return 50.0


def get_news_sentiment():
    """
    Very lightweight proxy:
    Pull top headlines count from a public RSS JSON mirror.
    Use volatility of headline lengths as emotional tension proxy.
    (Simple but effective for motion.)
    """
    try:
        url = "https://hnrss.org/frontpage.jsonfeed"
        r = requests.get(url, timeout=10)
        items = r.json().get("items", [])[:20]

        lengths = [len(item.get("title", "")) for item in items]
        if not lengths:
            return 50.0

        volatility = statistics.pstdev(lengths)

        # Map volatility ~10–40 → 30–70
        index = max(0, min(100, 50 + (volatility - 20)))
        return round(index, 2)

    except Exception:
        return 50.0


def compute_global_emotion():
    """
    Blend market + news.
    Market weighted slightly higher for stability.
    """
    market = get_market_sentiment()
    news = get_news_sentiment()

    blended = (market * 0.6) + (news * 0.4)

    summary = build_summary(blended, market, news)

    return round(blended, 2), summary


def build_summary(index, market, news):
    """
    Human-readable narrative.
    """
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


# ---------- Routes ----------

@app.route("/")
def root():
    return "Empath-Brain is running."


@app.route("/emotion")
def emotion():
    index, summary = compute_global_emotion()
    return jsonify({"index": index, "summary": summary})


@app.route("/narrative")
def narrative():
    index, summary = compute_global_emotion()
    return jsonify({"index": index, "summary": summary})


@app.route("/witness")
def witness():
    index, summary = compute_global_emotion()

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
                .index {{
                    margin-top: 20px;
                    font-size: 18px;
                    opacity: 0.6;
                }}
            </style>
        </head>
        <body>
            <div>
                {summary}
                <div class="index">Index: {index}</div>
            </div>
        </body>
    </html>
    """

    return Response(html, mimetype="text/html")


# ---------- Run ----------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
