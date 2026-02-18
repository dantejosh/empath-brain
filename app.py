import os
import requests
from flask import Flask, jsonify
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

app = Flask(__name__)

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
analyzer = SentimentIntensityAnalyzer()


def compute_emotion():
    if not NEWS_API_KEY:
        return 50.0, "Missing NEWS_API_KEY."

    url = "https://newsapi.org/v2/top-headlines"
    params = {"language": "en", "pageSize": 50, "apiKey": NEWS_API_KEY}

    try:
        r = requests.get(url, params=params, timeout=10)
        articles = r.json().get("articles", [])

        if not articles:
            return 50.0, "No articles returned."

        scores = []

        for a in articles:
            title = a.get("title", "")
            if title:
                sentiment = analyzer.polarity_scores(title)["compound"]
                scores.append(sentiment)

        if not scores:
            return 50.0, "No valid headlines."

        avg = sum(scores) / len(scores)

        # convert -1..1 → 0..100
        index = round((avg + 1) * 50, 2)

        # narrative tone
        if index < 40:
            summary = "Global emotional tone is tense and negative."
        elif index < 50:
            summary = "Global emotional tone is cautious and uneasy."
        elif index < 60:
            summary = "Global emotional tone is mixed and watchful."
        else:
            summary = "Global emotional tone is hopeful and constructive."

        return index, summary

    except Exception as e:
        return 50.0, f"Error: {str(e)}"


@app.route("/")
def root():
    return "Empath-Brain live."


@app.route("/emotion")
def emotion():
    index, summary = compute_emotion()
    return jsonify({
        "index": index,
        "summary": summary
    })


@app.route("/narrative")
def narrative():
    index, summary = compute_emotion()
    return jsonify({"text": summary})


@app.route("/witness")
def witness():
    index, summary = compute_emotion()
    return jsonify({"message": summary})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
