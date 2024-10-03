import json
import os
from flask import Flask, request, jsonify, render_template
import requests
import argparse

app = Flask(__name__)
OLLAMA_API_URL = "http://localhost:11434/api/generate"
HISTORY_FILE = "chat_history.json"

def load_chat_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []

def save_chat_history(history):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f)

def delete_chat_history():
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
        return True
    return False

chat_history = load_chat_history()

@app.route('/')
def index():
    return render_template('index.html', chat_history=chat_history)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data['message']
    chat_id = data.get('chatId')
    
    response = requests.post(OLLAMA_API_URL, json={
        "model": "tinydolphin:latest",
        "prompt": user_message,
        "stream": False
    })
    
    if response.status_code == 200:
        ai_response = response.json()['response']
        
        if chat_id is None:
            chat_label = user_message[:75] + "..." if len(user_message) > 75 else user_message
            new_chat = {
                "id": len(chat_history),
                "label": chat_label,
                "messages": []
            }
            chat_history.append(new_chat)
            chat_id = new_chat["id"]
        
        chat_history[chat_id]["messages"].extend([
            {"sender": "You", "message": user_message},
            {"sender": "AI", "message": ai_response}
        ])
        
        save_chat_history(chat_history)
        return jsonify({"response": ai_response, "chatId": chat_id})
    else:
        return jsonify({"error": "Failed to get response from Ollama"}), 500

@app.route('/delete-history', methods=['POST'])
def delete_history():
    if delete_chat_history():
        global chat_history
        chat_history = []
        return jsonify({"message": "Chat history deleted successfully"}), 200
    else:
        return jsonify({"message": "No chat history found to delete"}), 404

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run the chat application or delete chat history.")
    parser.add_argument('--delete-history', action='store_true', help="Delete the chat history")
    args = parser.parse_args()

    if args.delete_history:
        if delete_chat_history():
            print("Chat history deleted successfully.")
        else:
            print("No chat history found to delete.")
    else:
        app.run(debug=True)
