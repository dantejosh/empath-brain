from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "Empath-Brain is running."

@app.route("/emotion")
def emotion():
    return jsonify({
        "index": 43.06,
        "summary": "Test emotion endpoint is working."
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
