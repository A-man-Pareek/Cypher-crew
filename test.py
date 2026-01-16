import os
import requests
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "hackathon_secret_key")

# API Key Handling
raw_key = os.getenv("GEMINI_API_KEY")
API_KEY = raw_key.strip() if raw_key else None

# --- MODELS TO TRY (Based on your access) ---
MODELS_TO_TRY = [
    "gemini-2.5-flash",
    "gemini-2.0-flash", 
    "gemini-flash-latest"
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

    # --- KEYWORD DETECTION (For Visual Features) ---
    show_breathing = False
    show_yoga = False
    yoga_tip = ""
    msg_lower = user_message.lower()

    # Trigger Breathing for Stress/Anxiety
    if any(word in msg_lower for word in ["stress", "anxious", "panic", "scared", "nervous", "breathe", "help"]):
        show_breathing = True
    
    # Trigger Yoga for Pain/Tiredness
    if any(word in msg_lower for word in ["pain", "tired", "back", "yoga", "stiff", "neck", "hurt"]):
        show_yoga = True
        yoga_tip = "Try the 'Child Pose' or 'Neck Rolls' to release tension."

    # --- AI RESPONSE GENERATION ---
    active_reply = None
    
    # Context set karna taaki AI helpful reply kare
    context = "You are a supportive mental health assistant."
    if show_breathing:
        context += " The user is stressed. Kindly guide them to breathe."

    print(f"\n[USER]: {user_message}")

    for model_name in MODELS_TO_TRY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={API_KEY}"
            headers = {'Content-Type': 'application/json'}
            data = {
                "contents": [{"parts": [{"text": f"{context} User said: {user_message}. Reply in 2 sentences max."}]}]
            }

            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                active_reply = result['candidates'][0]['content']['parts'][0]['text']
                print(f"[SUCCESS] Connected to {model_name}")
                break
            else:
                print(f"[FAILED] {model_name} Status: {response.status_code}")
        
        except Exception as e:
            print(f"[ERROR] Connection failed on {model_name}")

    # --- FINAL RETURN ---
    return jsonify({
        "reply": active_reply if active_reply else "I am listening, but my connection is weak. Please try again.",
        "show_breathing": show_breathing,
        "show_yoga": show_yoga,
        "yoga_tip": yoga_tip
    })

if __name__ == '__main__':
    app.run(debug=True)