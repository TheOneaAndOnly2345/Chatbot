import os
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai

app = Flask(__name__)
genai.configure(api_key=os.getenv("AIzaSyDp5rrkwa7ndx9nbSUK_ltwKd-znQsYiuE"))
model = genai.GenerativeModel("gemini-1.5-flash")
chat = model.start_chat(history=[])

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat_endpoint():
    data = request.get_json()
    user_input = data.get("message", "")
    try:
        response = chat.send_message(user_input)
        return jsonify({"reply": response.text})
    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"}), 500

# ✅ This is the ONLY part changed for deployment:
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
