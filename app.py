import os
import requests
import datetime
from bson.objectid import ObjectId
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from dotenv import load_dotenv

# --- 1. IMPORT DATABASE HELPER ---
from database import db_helper 

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "hackathon_secret_key")

# API Key Handling
raw_key = os.getenv("GEMINI_API_KEY")
API_KEY = raw_key.strip() if raw_key else None

# --- 2. MODELS (Fixed: Using 1.5 to prevent crash/quota error) ---
MODELS_TO_TRY = ["gemini-2.5-flash", "gemini-2.5-pro"]

YOGA_SOLUTIONS = {
    "neck": {"tip": "Do 'Neck Rolls' to release tension.", "gif": "/static/neck.gif"},
    "back": {"tip": "Try 'Child Pose' for lower back relief.", "gif": "/static/back.gif"},
    "tired": {"tip": "A 'Seated Side Stretch' will wake you up.", "gif": "/static/tired.gif"},
    "stress": {"tip": "Sit straight and roll your shoulders back.", "gif": "/static/stress.gif"}
}

# --- 3. PAGE ROUTES ---

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('chat_page'))
    return redirect(url_for('login_page'))

@app.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect(url_for('chat_page'))
    return render_template('login.html')

@app.route('/register')
def register_page():
    if 'user_id' in session:
        return redirect(url_for('chat_page'))
    return render_template('register.html')

@app.route('/chat')
def chat_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('index.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

# --- 4. AUTHENTICATION APIs (Logic Updated for Redirect) ---

@app.route('/register_api', methods=['POST'])
def register_api():
    data = request.json
    print(f"Attempting to register: {data.get('username')}")
    
    user_id = db_helper.create_user(data.get('username'), data.get('password'))
    
    if user_id:
        # 🔥 FIX: Auto-Login (Session Set) taaki seedha chat khule
        session['user_id'] = str(user_id)
        return jsonify({"success": True, "message": "Registered successfully!"})
    
    return jsonify({"success": False, "message": "Username taken."})

@app.route('/login_api', methods=['POST'])
def login_api():
    data = request.json
    user = db_helper.verify_user(data.get('username'), data.get('password'))
    
    if user:
        # 🔥 FIX: Login Success hone par Session ID set karna zaroori hai
        session['user_id'] = str(user['_id'])
        return jsonify({"success": True, "message": "Login successful!"})
    
    return jsonify({"success": False, "message": "Invalid credentials."})

# --- 5. MAIN CHAT API ---

@app.route('/chat_api', methods=['POST'])
def chat_api():
    user_message = request.json.get('message')
    if not user_message: return jsonify({"reply": "Please type something."})
    
    if not API_KEY:
        print("[CRITICAL ERROR] API Key is missing in .env")
        return jsonify({"reply": "System Error: API Key missing."})

    msg_lower = user_message.lower()
    user_id = session.get('user_id', 'anonymous')

    # Triggers
    show_yoga, show_breathing = False, False
    yoga_data = {}
    mood_score, emotion_label = 5, "Neutral"

    if any(w in msg_lower for w in ["sad", "cry", "depressed", "lonely"]): 
        mood_score = 2; emotion_label = "Sad"
    elif any(w in msg_lower for w in ["happy", "great", "excited"]): 
        mood_score = 8; emotion_label = "Happy"
    elif any(w in msg_lower for w in ["angry", "mad"]): 
        mood_score = 1; emotion_label = "Angry"
    
    if any(w in msg_lower for w in ["stress", "anxious", "panic"]): 
        show_breathing = True; mood_score = 3; emotion_label = "Stressed"

    if any(w in msg_lower for w in ["pain", "neck", "back", "tired"]):
        show_yoga = True; mood_score = 4; emotion_label = "Physical Pain"
        if "neck" in msg_lower: yoga_data = YOGA_SOLUTIONS["neck"]
        elif "back" in msg_lower: yoga_data = YOGA_SOLUTIONS["back"]
        elif "stress" in msg_lower: yoga_data = YOGA_SOLUTIONS["stress"]
        else: yoga_data = YOGA_SOLUTIONS["tired"]

    # Save to DB
    try:
        db_helper.add_mood(user_id, mood_score, emotion_label, user_message)
    except Exception as e:
        print(f"[DATABASE ERROR] {e}")

    # AI Response
    active_reply = None
    context = "You are Serene, a supportive mental health assistant."
    if show_yoga: context += f" The user is in pain. Suggest {yoga_data.get('tip')}."
    if show_breathing: context += " The user is stressed. Guide them to breathe."

    print(f"\n[USER]: {user_message}")
    for model_name in MODELS_TO_TRY:
        try:
            print(f"[CONNECTING] to {model_name}...")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={API_KEY}"
            data = {"contents": [{"parts": [{"text": f"{context} User said: {user_message}. Reply kindly in 2 sentences."}]}]}
            response = requests.post(url, headers={'Content-Type': 'application/json'}, json=data)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result:
                    active_reply = result['candidates'][0]['content']['parts'][0]['text']
                    print(f"[SUCCESS] Connected to {model_name}")
                    break
            else:
                print(f"[GOOGLE REJECTED] {model_name} Status: {response.status_code}")
                
        except Exception as e:
            print(f"[CONNECTION ERROR] {model_name}: {e}")

    if not active_reply:
        active_reply = "I am listening. Take a deep breath. How can I help?"

    return jsonify({
        "reply": active_reply,
        "show_breathing": show_breathing,
        "show_yoga": show_yoga,
        "yoga_tip": yoga_data.get("tip", ""),
        "yoga_gif": yoga_data.get("gif", "")
    })

if __name__ == '__main__':
    app.run(debug=True)