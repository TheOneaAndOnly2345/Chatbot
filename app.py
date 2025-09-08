from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
import os
import base64

app = Flask(__name__)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")  # supports images
chat = model.start_chat(history=[])

@app.route("/nigganigganigga")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat_endpoint():
    user_input = request.form.get("message", "")
    image = request.files.get("image")

    try:
        if image:
            # Encode image as base64
            image_data = base64.b64encode(image.read()).decode("utf-8")
            mime_type = image.mimetype  # "image/png" or "image/jpeg"

            # Build the message in Gemini inline_data format
            parts = []
            if user_input:
                parts.append({"text": user_input})
            parts.append({"inline_data": {"mime_type": mime_type, "data": image_data}})

            response = chat.send_message([{"role": "user", "parts": parts}])
        else:
            response = chat.send_message(user_input)

        return jsonify({"reply": response.text})

    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
