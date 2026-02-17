import requests
from flask import Flask, jsonify, Response
from statistics import mean
import os
import time
from collections import deque

app = Flask(__name__)

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
NEWS_URL = "https://newsapi.org/v2/top-headlines?language=en&pageSize=10"
FEAR_GREED_URL = "https://api.alternative.me/fng/"

# ---------- emotional scoring ----------
POSITIVE = ["progress", "agreement", "recovery", "breakthrough", "stabilize"]
NEGATIVE = ["war", "flood", "crisis", "displace", "violence", "collapse", "fear"]


def score_text(text):
    score = 50
    t = text.lower()

    for w in POSITIVE:
        if w in t:
            score += 10
    for w in NEGATIVE:
        if w in t:
            score -= 10

    return max(0, min(100, score))


# ---------- data sources ----------
def get_fear_greed():
    try:
        r = requests.get(FEAR_GREED_URL, timeout=5)
        return float(r.json()["data"][0]["value"])
    except Exception:
        return 50.0


def get_headlines():
    try:
        r = requests.get(
            NEWS_URL,
            headers={"Authorization": NEWS_API_KEY},
            timeout=5,
        )
        data = r.json()
        return [a["title"] for a in data.get("articles", []) if a.get("title")]
    except Exception:
        return []


# ---------- emotional index ----------
def compute_index(headlines):
    structural = get_fear_greed()

    if headlines:
        narrative_scores = [score_text(h) for h in headlines]
        narrative = mean(narrative_scores)
    else:
        narrative = 50

    expressive = narrative

    return round(0.15 * structural + 0.30 * narrative + 0.55 * expressive, 2)


# ---------- trend memory ----------
HISTORY = deque(maxlen=12)  # last 12 hours


def detect_trend():
    if len(HISTORY) < 4:
        return ""

    short = HISTORY[-1] - HISTORY[-3]   # ~2-3 hours
    medium = HISTORY[-1] - HISTORY[0]   # ~6-12 hours

    # balanced sensitivity thresholds
    if abs(short) < 1.5 and abs(medium) < 2:
        return "holding steady"
    if short > 1.5 and medium > 2:
        return "slowly easing"
    if short < -1.5 and medium < -2:
        return "gently darkening"
    if abs(short) > 3:
        return "after recent instability"

    return ""


# ---------- narrative text ----------
def build_narrative(index, headlines):
    if index < 35:
        tone = "Global emotional tone is heavy and subdued"
    elif index < 55:
        tone = "Global emotional tone is cautious and uncertain"
    elif index < 70:
        tone = "Global emotional tone is steady with guarded optimism"
    else:
        tone = "Global emotional tone is broadly optimistic"

    trend = detect_trend()
    if trend:
        tone += f", {trend}"

    if not headlines:
        cause = "Current signals are mixed, with no single dominant event."
    else:
        ranked = sorted(headlines, key=lambda h: abs(score_text(h) - 50), reverse=True)
        selected = ranked[:2]
        cause = "Key drivers include: " + "; ".join(selected) + "."

    return f"{tone}. {cause}"


# ---------- hourly cache ----------
LAST_UPDATE_HOUR = None
CACHED_INDEX = 50.0
CACHED_SUMMARY = "Initializing global emotional state."


def get_hour():
    return int(time.time() // 3600)


def refresh_if_needed():
    global LAST_UPDATE_HOUR, CACHED_INDEX, CACHED_SUMMARY

    current_hour = get_hour()
    if LAST_UPDATE_HOUR == current_hour:
        return

    headlines = get_headlines()
    new_index = compute_index(headlines)

    HISTORY.append(new_index)

    # meaningful change threshold
    if abs(new_index - CACHED_INDEX) >= 2:
        CACHED_INDEX = new_index
        CACHED_SUMMARY = build_narrative(new_index, headlines)

    LAST_UPDATE_HOUR = current_hour


# ---------- routes ----------
@app.route("/emotion")
def emotion():
    refresh_if_needed()
    return jsonify({"index": CACHED_INDEX})


@app.route("/narrative")
def narrative():
    refresh_if_needed()
    return jsonify({"index": CACHED_INDEX, "summary": CACHED_SUMMARY})


@app.route("/witness")
def witness():
    refresh_if_needed()

    if CACHED_INDEX < 50:
        bg, fg = "#0b1a2a", "#e8f0ff"
    else:
        bg, fg = "#1a140b", "#fff6e8"

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
                opacity: 0.92;
            }}
        </style>
    </head>
    <body>
        <div class="text">{CACHED_SUMMARY}</div>
    </body>
    </html>
    """

    return Response(html, mimetype="text/html")


@app.route("/")
def home():
    return "Empath brain running."
