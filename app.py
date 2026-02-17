from flask import Flask, jsonify, Response

app = Flask(__name__)

@app.route("/")
def home():
    return "Empath brain running."

@app.route("/emotion")
def emotion():
    return jsonify({"index": 50.0})

@app.route("/narrative")
def narrative():
    return jsonify({
        "index": 50.0,
        "summary": "System stabilizing. Emotional sensing initializing."
    })

@app.route("/witness")
def witness():
    html = """
    <html>
    <body style="
        margin:0;
        background:#111;
        color:#eee;
        display:flex;
        align-items:center;
        justify-content:center;
        height:100vh;
        font-family:sans-serif;
        text-align:center;
        padding:2rem;
    ">
        <div>System stabilizing.<br>Emotional sensing initializing.</div>
    </body>
    </html>
    """
    return Response(html, mimetype="text/html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)


