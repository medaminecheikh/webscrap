from flask import Flask, request, jsonify
from textblob import TextBlob
app = Flask(__name__)

@app.route("/sentiment", methods=["POST"])
def sentiment():
    data = request.json
    analysis = TextBlob(data["text"])
    return jsonify({"polarity": analysis.sentiment.polarity})

if __name__ == "__main__":
    app.run(port=5000)
