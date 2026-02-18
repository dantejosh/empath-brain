import threading
import time
from datetime import datetime
import random

from flask import Flask, jsonify

app = Flask(__name__)

# ---------- GLOBAL STATE ----------
CURRENT_INDEX = 50.0
CURRENT_SUMMARY = "Initializing global emotional state..."
LAST_UPDATE = None


# ---------- EMOTION ENGINE ----------
def compute_global_emotion():
    """
    Placeholder emotion computation.
    Replace later with real news / sentiment sources.
    """

    # simulate real-world fluctuation
    index = round(random.uniform(35, 65), 2)

    if index < 40:
        summary = "Global emotional tone is tense and unstable."
    elif index < 50:
        summary = "Global emotional tone is cautious and uncertain."
    elif index < 60:
        summary = "Global emotional tone is balanced with mixed signals."
    else:
        summary = "Global emotional tone is optimistic and forward-leaning."

    return index, summary


# ---------- BACKGROUND UPDATER ----------
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

        # wait 1 hour before next update
        time.sleep(3600)


# ---------- STARTUP: RUN FIRST UPDATE IMMEDIATELY ----------
def initialize_emotion():
    global CURRENT_INDEX, CURRENT_SUMMARY, LAST_UPDATE

    try:
        index, summary = compute_global_emotion()
        CURRENT_INDEX = index
        CURRENT_SUMMARY = summary
        LAST_UPDATE = datetime.utcnow().isoformat()
        print(f"[INIT] {LAST_UPDATE} → {index}")
    except Exception as e:
        print("Initialization error:", e)


initialize_emotion()
threading.Thread(target=emotion_updater, daemon=True).start()


# ---------- ROUTES ----------
@app.route("/")
def home():
    return "Empath-Brain is running."


@app.route("/emotion")
def emotion():
    return jsonify({
        "index": CURRENT_INDEX,
        "last_update": LAST_UPDATE,
        "summary": CURRENT_SUMMARY
    })


@app.route("/narrative")
def narrative():
    return jsonify({
        "text": CURRENT_SUMMARY
    })


@app.route("/witness")
def witness():
    return jsonify({
        "message": CURRENT_SUMMARY
    })


# ---------- RUN ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
