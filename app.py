from flask import Flask, jsonify, Response
import os
import time
from collections import deque

app = Flask(__name__)

# --------------------------------------------------
# Simple in-memory emotional model (stable baseline)
# --------------------------------------------------

CACHED_INDEX = 43.0
CACHED_SUMMARY = "Global emotional tone is cautious and uncertain."

HISTORY = deque(maxlen=12)  # last 12 hourly values
LAST_UPDATE_HOUR = None


def get_hour():
    return int(time.time() // 3600)


def detect_trend():
    if len(HISTORY) < 4:
        return ""

    short = HISTORY[-1] - HISTORY[-3]
    medium = HISTORY[-1] - HISTORY[0]

    if abs(short) < 1.5 and abs(medium) < 2:
        return "holding steady"
    if short > 1.5 and medium > 2:
        return "slowly easing"
    if short < -1.5 and medium < -2:
        return "gently darkening"
    if abs(short) > 3:
        return "after recent instability"

    return ""


def refresh_if_needed():
    global LAST_UPDATE_HOUR, CACHED_INDEX, CACHED_SUMMARY

    current_hour = get_hour()
    if LAST_UPDATE_HOUR == current_hour:
        return

    # --- simulated gentle drift for stability ---
    import random
    drift = random.uniform(-1.5, 1.5)
    new_index = max(0, min(100, CACHED_INDEX + drift))

    HISTORY.append(new_index)

    if abs(new_index - CACHED_INDEX) >= 1:
        CACHED_INDEX = round(new_index, 2)

        tone = "Global emotional tone is cautious and uncertain"
        trend = detect_trend()
        if trend:
            tone += f", {trend}"

        CACHED_SUMMARY = tone + "."

    LAST_UPDATE_HOUR = current_hour


# --------------------------------------------------
# Routes
# --------------------------------------------------

@app.route("/")
def home():
    return "Empath-Brain is running."


@app.route("/emotion")
def emotion():
    refresh_if_needed()
    return jsonify({"index": CACHED_INDEX, "summary": CACHED_SUMMARY})


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


# --------------------------------------------------
# Local run support (ignored by Render)
# --------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
