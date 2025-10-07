from flask import Flask, request, jsonify, render_template, Response
import google.generativeai as genai
import os
import base64
import re
import json
import time

app = Flask(__name__)
genai.configure(api_key=os.getenv("AIzaSyBxdmmCHhSV-ZNmTP8FJY43uzLgsK_vR1Q"))

model = genai.GenerativeModel("gemini-flash-latest")
  # supports images
chat = model.start_chat(history=[])

@app.route("/")
def index():
    return render_template("index.html")

def format_response_text(text):
    """Convert markdown-like formatting to HTML"""
    text = text or ""  # fallback in case Gemini returns None

    # Handle the specific pattern ***Word:** that appears in your text
    text = re.sub(r'\*\*\*([^*:]+?):', r'<strong>\1:</strong>', text)

    # Handle any remaining ***text*** patterns  
    text = re.sub(r'\*\*\*([^*]+?)\*\*\*', r'<strong>\1</strong>', text)

    # Handle **text** patterns
    text = re.sub(r'\*\*([^*]+?)\*\*', r'<strong>\1</strong>', text)

    # Handle single *text* patterns
    text = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<em>\1</em>', text)

    # Convert line breaks to <br> tags
    text = text.replace('\n', '<br>')

    # Add line breaks after strong tags for better formatting
    text = re.sub(r'</strong>([A-Z])', r'</strong><br>\1', text)

    return text

def stream_words(text, delay=0.03):
    """Generator that yields words one at a time for SSE - FIXED VERSION"""
    # Split the text in a way that preserves HTML tags
    # Use regex to split by spaces but keep HTML tags together
    parts = re.findall(r'<[^>]+>|[^<\s]+|\s+', text)
    
    current_text = ""
    word_buffer = ""

    for part in parts:
        # Add to buffer
        word_buffer += part
        
        # Only send update when we hit a space or end
        if part.strip() and not part.startswith('<'):
            current_text = word_buffer.strip()
            data = {
                "word": part.strip(),
                "current_text": current_text,
                "complete": False
            }
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(delay)

    # Send completion signal
    final_data = {
        "word": "",
        "current_text": word_buffer.strip(),
        "complete": True
    }
    yield f"data: {json.dumps(final_data)}\n\n"

@app.route("/chat", methods=["POST"])
def chat_endpoint():
    user_input = request.form.get("message", "")
    image = request.files.get("image")
    stream = request.form.get("stream", "true").lower() == "true"

    try:
        if image:
            # Encode image as base64
            image_data = base64.b64encode(image.read()).decode("utf-8")
            mime_type = image.mimetype  # "image/png" or "image/jpeg"

            # Build the message parts
            parts = []
            if user_input:
                parts.append({"text": user_input})
            parts.append({"inline_data": {"mime_type": mime_type, "data": image_data}})

            response = chat.send_message(parts)
        else:
            response = chat.send_message(user_input)

        # Format the response text
        reply_text = response.text or ""
        formatted_reply = format_response_text(reply_text)

        if stream:
            return Response(
                stream_words(formatted_reply, delay=0.03),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Access-Control-Allow-Origin': '*'
                }
            )
        else:
            return jsonify({"reply": formatted_reply})

    except Exception as e:
        error_data = {"reply": f"Error: {str(e)}", "complete": True}
        if stream:
            return Response(
                f"data: {json.dumps(error_data)}\n\n",
                mimetype='text/event-stream'
            )
        else:
            return jsonify(error_data), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)