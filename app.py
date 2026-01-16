import os
import requests
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "hackathon_secret_key"

# Clean the key in case of accidental spaces
raw_key = os.getenv("GEMINI_API_KEY")
API_KEY = raw_key.strip() if raw_key else None

# List of models to try
MODELS_TO_TRY = [
    "gemini-2.5-flash",
    "gemini-pro",
    "gemini-2.5-pro-latest"
]

@app.route('/')
def home():
    if 'user_id' not in session:
        session['user_id'] = os.urandom(4).hex()
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"reply": "Please type something."})
    
    if not API_KEY:
        return jsonify({"reply": "CRITICAL ERROR: API Key is missing in .env file."})

    active_reply = None
    debug_log = [] # We will store errors here to show you

    print(f"\n[USER]: {user_message}")

    # --- LOOP THROUGH MODELS ---
    for model_name in MODELS_TO_TRY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={API_KEY}"
            
            headers = {'Content-Type': 'application/json'}
            data = {
                "contents": [{"parts": [{"text": f"User said: {user_message}. Reply kindly as a mental health assistant in 2 sentences."}]}]
            }

            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                active_reply = result['candidates'][0]['content']['parts'][0]['text']
                print(f"[SUCCESS] Connected to {model_name}")
                break
            else:
                # Store the error to show the user
                error_msg = f"{model_name} Failed ({response.status_code}): {response.text}"
                print(f"[GOOGLE REJECTED] {error_msg}")
                debug_log.append(error_msg)
        
        except Exception as e:
            error_msg = f"{model_name} Error: {str(e)}"
            print(f"[CONNECTION ERROR] {error_msg}")
            debug_log.append(error_msg)

    # --- RESULT ---
    if active_reply:
        return jsonify({"reply": active_reply})
    else:
        # RETURN THE REAL ERROR TO THE BROWSER
        error_summary = " | ".join(debug_log)
        return jsonify({"reply": f"GOOGLE ERROR: {error_summary}"})

if __name__ == '__main__':
    app.run(debug=True)