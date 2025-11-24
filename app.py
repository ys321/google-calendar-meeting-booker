from __future__ import annotations

from flask import Flask, jsonify, render_template, request, session, redirect, url_for
from flask_cors import CORS
from langchain_core.messages import HumanMessage, AIMessage

from config import SECRET_KEY
from chatbot import build_agent
from google_oauth import create_flow, save_credentials

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = SECRET_KEY
CORS(app)

# Build a single global agent instance
agent = build_agent()


@app.route("/")
def index():
    """
    Simple test page for the chatbot.
    """
    return render_template("index.html")

@app.route("/auth/google")
def auth_google():
    """
    Start Google OAuth flow for Calendar + Meet.
    """
    flow = create_flow()
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    session["oauth_state"] = state
    return redirect(authorization_url)


@app.route("/auth/google/callback")
def auth_google_callback():
    """
    OAuth callback: exchange code for tokens and save them.
    """
    state = session.get("oauth_state")
    flow = create_flow(state=state)
    flow.fetch_token(authorization_response=request.url)

    creds = flow.credentials
    save_credentials(creds)

    # Simple redirect back to chat page with a message
    return redirect(url_for("index"))

@app.route("/api/chat", methods=["POST"])
def chat_api():
    data = request.get_json(force=True)
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"reply": "Please type a message."}), 400

    try:
        # Get chat history from session (simple in-memory storage)
        # Store as list of dicts for serialization
        if "messages" not in session:
            session["messages"] = []
        
        # Convert stored dicts back to message objects
        messages_dicts = session["messages"]
        messages = []
        for msg_dict in messages_dicts:
            if msg_dict["type"] == "human":
                messages.append(HumanMessage(content=msg_dict["content"]))
            elif msg_dict["type"] == "ai":
                messages.append(AIMessage(content=msg_dict["content"]))
        
        # Add the new user message
        messages.append(HumanMessage(content=user_message))
        
        # Invoke agent with messages (new API format)
        result = agent.invoke({"messages": messages})
        
        # Extract the last AI message from the result
        output_messages = result.get("messages", [])
        
        # Find the last AI message (skip tool messages)
        ai_messages = []
        for msg in output_messages:
            if isinstance(msg, AIMessage):
                ai_messages.append(msg)
        
        if ai_messages:
            # Get the last AI message content
            last_ai_msg = ai_messages[-1]
            # Handle content that might be a string, list, or object
            if isinstance(last_ai_msg.content, str):
                reply = last_ai_msg.content
            elif isinstance(last_ai_msg.content, list):
                # Extract text from content blocks (handle dict items in list)
                text_parts = []
                for item in last_ai_msg.content:
                    if isinstance(item, str):
                        text_parts.append(item)
                    elif isinstance(item, dict):
                        # Extract text from dict if it has a 'text' key
                        text_parts.append(item.get('text', str(item)))
                    else:
                        text_parts.append(str(item))
                reply = " ".join(text_parts) if text_parts else "I received a response but couldn't parse it."
            elif isinstance(last_ai_msg.content, dict):
                # Extract text from dict if it has a 'text' key
                reply = last_ai_msg.content.get('text', str(last_ai_msg.content))
            else:
                reply = str(last_ai_msg.content) if last_ai_msg.content else "I received an empty response."
        else:
            # Fallback: try to extract any useful information
            reply = "I'm sorry, I couldn't generate a response. Please try again."
            print(f"Warning: No AI messages found in result. Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        
        # Update session with all messages (including the new ones)
        messages_dicts = []
        for msg in output_messages:
            if isinstance(msg, HumanMessage):
                content = msg.content if isinstance(msg.content, str) else str(msg.content)
                messages_dicts.append({"type": "human", "content": content})
            elif isinstance(msg, AIMessage):
                content = msg.content if isinstance(msg.content, str) else str(msg.content)
                messages_dicts.append({"type": "ai", "content": content})
        session["messages"] = messages_dicts
        
    except Exception as e:
        print("Agent error:", e)
        import traceback
        traceback.print_exc()
        reply = (
            "Sorry, something went wrong while processing your request. "
            "Please try again in a moment."
        )

    # Ensure reply is always a string
    if not isinstance(reply, str):
        reply = str(reply)
    
    return jsonify({"reply": reply})


if __name__ == "__main__":
    # Local development
    app.run(host="0.0.0.0", port=5000, debug=True)
