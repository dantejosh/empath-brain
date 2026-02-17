import requests
from flask import Flask, jsonify
from statistics import mean

app = Flask(__name__)

FEAR_GREED_URL = "https://api.alternative.me/fng/"

# --- Simple headline sample (temporary narrative proxy) ---
HEADLINES = [
    "Ceasefire talks show cautious progress",
    "Severe flooding displaces thousands",
    "Global markets stabilize after volatility",
    "Breakthrough in renewable energy research",
    "Rising food insecurity concerns aid groups",
]

# --- Very lightweight sentiment scoring ---
def score_text(text):
    positive_words = ["progress", "stabilize", "breakthrough"]
    negative_words = ["flooding", "displaces", "insecurity", "volatility"]

    score = 50

    for w in positive_words:
        if w in text.lower():
            score += 10
    for w in negative_words:
        if w in text.lower():
            score -= 10

    return max(0, min(100, score))


# --- Structural mood ---
def get_fear_greed():
    try:
        r = requests.get(FEAR_GREED_URL, timeout=5)
        data = r.json()
        return float(data["data"][0]["value"])
    except Exception:
        return 50.0


# --- Narrative mood ---
def narrative_index():
    scores = [score_text(h) for h in HEADLINES]
    return mean(scores)


# --- Empath fusion ---
def empath_index():
    structural = get_fear_greed()
    narrative = narrative_index()
    expressive = narrative  # placeholder for future AI layer

    return round(
        0.15 * structural +
        0.30 * narrative +
        0.55 * expressive,
        2
    )


# --- Calm narrative summary ---
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
    return jsonify({
        "index": idx,
        "summary": build_narrative(idx)
    })


@app.route("/")
def home():
    return "Empath brain running."


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
