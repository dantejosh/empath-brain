from flask import Flask, jsonify, render_template_string
import datetime
import random

app = Flask(__name__)

# -------------------------------------------------------------------
# SIMPLE STABLE EMOTION MODEL
# -------------------------------------------------------------------

def compute_emotion():
    """
    Lightweight, stable placeholder logic.
    Replace later with real news + market inputs without
    changing any routes.
    """

    # gentle drift around mid-range to avoid frozen feeling
    base = 50
    drift = random.randint(-5, 5)

    index = max(0, min(100, base + drift))

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

    return index, summary


# -------------------------------------------------------------------
# JSON ENDPOINT FOR ESP32
# -------------------------------------------------------------------

@app.route("/emotion")
def emotion():
    index, summary = compute_emotion()
    return jsonify({
        "index": index,
        "summary": summary
    })


# -------------------------------------------------------------------
# QUIET MUSEUM-STYLE WITNESS PAGE
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
        Observed {{ timestamp }} UTC
    </div>
</div>
</body>
</html>
"""


@app.route("/witness")
def witness():
    index, summary = compute_emotion()
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")

    return render_template_string(
        WITNESS_TEMPLATE,
        index=index,
        summary=summary,
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
