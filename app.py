import requests
from flask import Flask, jsonify, Response
from statistics import mean

app = Flask(__name__)

FEAR_GREED_URL = "https://api.alternative.me/fng/"

HEADLINES = [
    "Ceasefire talks show cautious progress",
    "Severe flooding displaces thousands",
    "Global markets stabilize after volatility",
    "Breakthrough in renewable energy research",
    "Rising food insecurity concerns aid groups",
]


def score_text(text):
    positive = ["progress", "stabilize", "breakthrough"]
    negative = ["flooding", "displaces", "insecurity", "volatility"]

    score = 50
    for w in positive:
        if w in text.lower():
            score += 10
    for w in negative:
        if w in text.lower():
            score -= 10

    return max(0, min(100, score))


def get_fear_greed():
    try:
        r = requests.get(FEAR_GREED_URL, timeout=5)
        return float(r.json()["data"][0]["value"])
    except Exception:
        return 50.0


def narrative_index():
    return mean(score_text(h) for h in HEADLINES)


def empath_index():
    structural = get_fear_greed()
    narrative = narrative_index()
    expressive = narrative

    return round(0.15 * structural + 0.30 * narrative + 0.55 * expressive, 2)


def build_narrative(index):
    if index < 35:
        tone = "Global emotional tone feels heavy and subdued."
    elif index < 55:
        tone = "Global emotional tone is quiet and uncertain."
    elif index < 70:
        tone = "Global emotional tone shows cautious steadiness."
    else:
        tone = "Global emotional tone carries gentle optimism."

    return tone + " The feeling emerges from a mix of hardship, recovery, and fragile stability across regions."


@app.route("/emotion")
def emotion():
    return jsonify({"index": empath_index()})


@app.route("/narrative")
def narrative():
    idx = empath_index()
    return jsonify({"index": idx, "summary": build_narrative(idx)})


# ---------- NEW WITNESS PAGE ----------
@app.route("/witness")
def witness():
    idx = empath_index()
    summary = build_narrative(idx)

    # map emotion to soft background color
    if idx < 50:
        bg = "#0b1a2a"   # deep indigo
        fg = "#e8f0ff"
    else:
        bg = "#1a140b"   # warm dusk amber
        fg = "#fff6e8"

    html = f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                margin: 0;
                background: {bg};
                color: {fg};
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100vh;
                text-align: center;
                padding: 2rem;
            }}
            .text {{
                font-size: 1.4rem;
                line-height: 1.6;
                max-width: 32rem;
                opacity: 0.9;
            }}
        </style>
    </head>
    <body>
        <div class="text">{summary}</div>
    </body>
    </html>
    """

    return Response(html, mimetype="text/html")


@app.route("/")
def home():
    return "Empath brain running."

