import os
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai

app = Flask(__name__)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")
chat = model.start_chat(history=[])

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat_endpoint():
    data = request.get_json()
    user_input = data.get("message", "")

    banned_words = ["nigger", "nigga", "Nigga", "Nigger"]  

    try:
        response = chat.send_message(user_input)
        reply_text = response.text.lower()

        if any(banned_word in reply_text for banned_word in banned_words):
            return jsonify({"reply": "I'm sorry, that is not within the TOS that I have not mentioned before."})

        return jsonify({"reply": response.text})

    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
