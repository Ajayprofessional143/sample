# app.py
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template_string

# LangChain Groq imports (same as your previous code)
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

# Load env
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Initialize LLM (will raise if API key missing)
llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.1-8b-instant",
)

# Single-file HTML template (rendered via render_template_string)
HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Groq Chat — Single File</title>
  <style>
    body { font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial; background: #f5f7fb; color:#111; margin:0; padding:0; display:flex; align-items:center; justify-content:center; height:100vh; }
    .container { width:100%; max-width:800px; background:#fff; border-radius:12px; box-shadow:0 6px 24px rgba(15,23,42,0.08); padding:18px; display:flex; flex-direction:column; height:80vh; }
    header { display:flex; align-items:center; gap:12px; margin-bottom:12px; }
    header h1 { font-size:1.1rem; margin:0; }
    #chat { flex:1; overflow:auto; padding:12px; border:1px solid #eef2f7; border-radius:8px; background:#fbfdff; }
    .msg { margin:8px 0; display:flex; gap:10px; align-items:flex-start; }
    .msg.user { justify-content:flex-end; }
    .bubble { padding:10px 14px; border-radius:12px; max-width:75%; box-shadow:0 1px 0 rgba(0,0,0,0.03); }
    .bubble.user { background:#0ea5a3; color:white; border-bottom-right-radius:4px; }
    .bubble.bot  { background:#f1f7ff; color:#0b1220; border-bottom-left-radius:4px; }
    .controls { display:flex; gap:8px; margin-top:12px; }
    textarea { flex:1; resize:none; padding:10px; border-radius:8px; border:1px solid #e6eef7; min-height:56px; font-size:0.95rem; }
    button { padding:10px 14px; background:#0ea5a3; color:white; border:none; border-radius:8px; cursor:pointer; font-weight:600; }
    button[disabled] { opacity:0.6; cursor:not-allowed; }
    .meta { font-size:0.85rem; color:#667085; margin-left:auto; }
    .small { font-size:0.85rem; color:#94a3b8; margin-top:8px; }
  </style>
</head>
<body>
  <div class="container" role="main">
    <header>
      <svg width="36" height="36" viewBox="0 0 24 24" fill="none" aria-hidden><path d="M3 12a9 9 0 1018 0 9 9 0 00-18 0z" fill="#0ea5a3"/></svg>
      <h1>Groq Chat (single-file Flask)</h1>
      <div class="meta">Local demo</div>
    </header>

    <div id="chat" aria-live="polite"></div>

    <div class="controls">
      <textarea id="message" placeholder="Type your message..." aria-label="Message"></textarea>
      <button id="send">Send</button>
    </div>
    <div class="small">Press Enter + Shift to insert newline. Press Ctrl+Enter (or click Send) to send.</div>
  </div>

<script>
const chatEl = document.getElementById('chat');
const inputEl = document.getElementById('message');
const sendBtn = document.getElementById('send');

function appendMessage(text, who='bot') {
  const wrapper = document.createElement('div');
  wrapper.className = 'msg ' + (who === 'user' ? 'user' : 'bot');
  const bubble = document.createElement('div');
  bubble.className = 'bubble ' + (who === 'user' ? 'user' : 'bot');
  bubble.textContent = text;
  wrapper.appendChild(bubble);
  chatEl.appendChild(wrapper);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function setSending(isSending){
  sendBtn.disabled = isSending;
  inputEl.disabled = isSending;
  sendBtn.textContent = isSending ? 'Sending...' : 'Send';
}

async function sendMessage() {
  const text = inputEl.value.trim();
  if (!text) return;
  appendMessage(text, 'user');
  inputEl.value = '';
  setSending(true);

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ message: text })
    });

    if (!res.ok) {
      const err = await res.json().catch(()=>({error:'unknown'}));
      appendMessage('Error: ' + (err.error || err.details || 'Request failed'), 'bot');
      setSending(false);
      return;
    }

    const data = await res.json();
    if (data.bot) {
      appendMessage(data.bot, 'bot');
    } else if (data.error) {
      appendMessage('Error: ' + data.error, 'bot');
    } else {
      appendMessage('No response from server.', 'bot');
    }
  } catch (e) {
    appendMessage('Network error: ' + e.message, 'bot');
  } finally {
    setSending(false);
  }
}

// keyboard shortcuts
inputEl.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    e.preventDefault();
    sendMessage();
  }
  // Allow Shift+Enter for newline
});

// send button
sendBtn.addEventListener('click', sendMessage);

// focus
inputEl.focus();
</script>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Missing 'message' field"}), 400

    user_message = data["message"]

    try:
        # Call the Groq LLM via LangChain wrapper
        response = llm.invoke([HumanMessage(content=user_message)])
        return jsonify({
            "user": user_message,
            "bot": response.content
        })
    except Exception as e:
        # Return error details for debugging (remove details in production)
        return jsonify({"error": "LLM request failed", "details": str(e)}), 500

if __name__ == "__main__":
    # Host 0.0.0.0 so you can access from other devices if needed
    app.run(host="0.0.0.0", port=5000, debug=True)
