import os
import requests
import datetime
from bson.objectid import ObjectId
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv

# --- 1. DATABASE HELPER ---
from database import db_helper 

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "hackathon_secret_key")

# API Key Handling
raw_key = os.getenv("GEMINI_API_KEY")
API_KEY = raw_key.strip() if raw_key else None

# --- 2. MODELS & DATA ---
MODELS_TO_TRY = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest", "gemini-pro"]

YOGA_SOLUTIONS = {
    "neck": {"tip": "Do 'Neck Rolls' to release tension.", "gif": "/static/neck.gif"},
    "back": {"tip": "Try 'Child Pose' for lower back relief.", "gif": "/static/back.gif"},
    "tired": {"tip": "A 'Seated Side Stretch' will wake you up.", "gif": "/static/tired.gif"},
    "stress": {"tip": "Sit straight and roll your shoulders back.", "gif": "/static/stress.gif"}
}

# --- 3. ROUTES ---

@app.route('/')
def home():
    if 'user_id' not in session:
        # AB HUM ASLI MONGODB ID BANA RAHE HAIN
        session['user_id'] = str(ObjectId()) 
    return render_template('index.html')
# --- AUTHENTICATION ROUTES ---
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    user_id = db_helper.create_user(data.get('username'), data.get('password'))
    if user_id:
        session['user_id'] = user_id
        return jsonify({"success": True, "message": "Registered successfully!"})
    return jsonify({"success": False, "message": "Username taken."})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = db_helper.verify_user(data.get('username'), data.get('password'))
    if user:
        session['user_id'] = str(user['_id'])
        return jsonify({"success": True, "message": "Login successful!"})
    return jsonify({"success": False, "message": "Invalid credentials."})

# --- MAIN CHAT ROUTE ---
@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"reply": "Please type something."})
    
    if not API_KEY:
        print("[CRITICAL ERROR] API Key is missing in .env")
        return jsonify({"reply": "System Error: API Key missing."})

    msg_lower = user_message.lower()
    user_id = session.get('user_id', 'anonymous')

    # --- 4. DETECT VISUAL TRIGGERS ---
    show_yoga = False
    show_breathing = False
    yoga_data = {}
    
    mood_score = 5 
    emotion_label = "Neutral"

    if any(w in msg_lower for w in ["sad", "cry", "depressed", "lonely"]):
        mood_score = 2; emotion_label = "Sad"
    elif any(w in msg_lower for w in ["happy", "great", "excited"]):
        mood_score = 8; emotion_label = "Happy"
    elif any(w in msg_lower for w in ["angry", "mad", "furious"]):
        mood_score = 1; emotion_label = "Angry"
    
    if any(w in msg_lower for w in ["stress", "anxious", "panic", "worry"]):
        show_breathing = True
        mood_score = 3; emotion_label = "Stressed"

    if any(w in msg_lower for w in ["pain", "neck", "back", "tired"]):
        show_yoga = True
        mood_score = 4; emotion_label = "Physical Pain"
        if "neck" in msg_lower: yoga_data = YOGA_SOLUTIONS["neck"]
        elif "back" in msg_lower: yoga_data = YOGA_SOLUTIONS["back"]
        elif "stress" in msg_lower: yoga_data = YOGA_SOLUTIONS["stress"]
        else: yoga_data = YOGA_SOLUTIONS["tired"]

    # --- 5. SAVE TO MONGODB ---
    try:
        db_helper.add_mood(user_id, mood_score, emotion_label, user_message)
        print(f"[DATABASE] Mood Logged: {emotion_label}")
    except Exception as e:
        print(f"[DATABASE ERROR] {e}")

    # --- 6. AI RESPONSE (DEBUG MODE ON - NO EMOJIS) ---
    active_reply = None
    context = "You are Serene, a supportive mental health assistant."
    if show_yoga: context += f" The user is in pain. Suggest {yoga_data.get('tip')}."
    if show_breathing: context += " The user is stressed. Guide them to breathe."

    print(f"\n[USER]: {user_message}")
    print(f"[DEBUG] API Key Loaded: {'Yes' if API_KEY else 'No'}") 

    for model_name in MODELS_TO_TRY:
        try:
            print(f"[CONNECTING] to {model_name}...")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={API_KEY}"
            headers = {'Content-Type': 'application/json'}
            data = {"contents": [{"parts": [{"text": f"{context} User said: {user_message}. Reply kindly in 2 sentences."}]}]}
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result:
                    active_reply = result['candidates'][0]['content']['parts'][0]['text']
                    print(f"[SUCCESS] Connected to {model_name}")
                    break
            else:
                # YAHAN ERROR PRINT HOGA
                print(f"[GOOGLE REJECTED] {model_name} Status: {response.status_code}")
                print(f"Reason: {response.text}") 
                
        except Exception as e:
            print(f"[CONNECTION ERROR] {model_name}: {e}")

    if not active_reply:
        active_reply = "I am listening. Take a deep breath. How can I help?"

    # --- 7. RETURN RESPONSE ---
    return jsonify({
        "reply": active_reply,
        "show_breathing": show_breathing,
        "show_yoga": show_yoga,
        "yoga_tip": yoga_data.get("tip", ""),
        "yoga_gif": yoga_data.get("gif", "")
    })

if __name__ == '__main__':
    app.run(debug=True) 