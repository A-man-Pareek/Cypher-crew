import os
import requests
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from dotenv import load_dotenv
from database import db_helper 

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "super_secret_key_change_me")

# API Key Check
raw_key = os.getenv("GEMINI_API_KEY")
API_KEY = raw_key.strip() if raw_key else None
MODELS_TO_TRY = ["gemini-1.5-flash", "gemini-1.5-pro"]

YOGA_SOLUTIONS = {
    "neck": {"tip": "Neck Rolls", "gif": "/static/neck.gif"},
    "back": {"tip": "Child Pose", "gif": "/static/back.gif"},
    "tired": {"tip": "Side Stretch", "gif": "/static/tired.gif"},
    "stress": {"tip": "Shoulder Roll", "gif": "/static/stress.gif"}
}

# --- ROUTES ---
@app.route('/')
def index():
    return redirect(url_for('chat_page') if 'user_id' in session else 'login_page')

@app.route('/login')
def login_page():
    return redirect(url_for('chat_page')) if 'user_id' in session else render_template('login.html')

@app.route('/register')
def register_page():
    return redirect(url_for('chat_page')) if 'user_id' in session else render_template('register.html')

@app.route('/chat')
def chat_page():
    return render_template('index.html') if 'user_id' in session else redirect(url_for('login_page'))

@app.route('/insight')
def insight_page():
    return render_template('insight.html') if 'user_id' in session else redirect(url_for('login_page'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

# --- APIs ---
@app.route('/login_api', methods=['POST'])
def login_api():
    data = request.json
    user = db_helper.verify_user(data.get('username'), data.get('password'))
    if user:
        session['user_id'] = str(user['_id'])
        return jsonify({"success": True})
    return jsonify({"success": False})

@app.route('/register_api', methods=['POST'])
def register_api():
    data = request.json
    uid = db_helper.create_user(data.get('username'), data.get('password'))
    if uid:
        session['user_id'] = str(uid)
        return jsonify({"success": True})
    return jsonify({"success": False})

@app.route('/get_history_api', methods=['GET'])
def get_history_api():
    if 'user_id' not in session: return jsonify({"success": False})
    # Error Handling included here
    try:
        history = db_helper.get_chat_history(session['user_id'])
        return jsonify({"success": True, "history": history})
    except Exception as e:
        print(f"History Error: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/insight_api')
def insight_api():
    if 'user_id' not in session: return jsonify({"success": False})
    data = db_helper.get_user_insights(session['user_id'])
    return jsonify({"success": True, "data": data}) if data else jsonify({"success": False})

@app.route('/chat_api', methods=['POST'])
def chat_api():
    data = request.json
    user_message = data.get('message', '')
    is_venting = data.get('is_venting', False)

    # 🔥 FIX: Initialize variables at the TOP so they are never undefined
    show_yoga = False
    yoga_tip = ""
    yoga_gif = ""
    reply = "I am listening."

    if not user_message: return jsonify({"reply": "Please type something."})
    
    uid = session.get('user_id')
    msg_lower = user_message.lower()
    
    # 1. Breathing Check
    if session.get('waiting_for_breathing'):
        session.pop('waiting_for_breathing')
        if any(w in msg_lower for w in ["yes", "ok", "sure", "do it"]):
            return jsonify({
                "reply": "Starting breathing exercise...", 
                "show_breathing": True,
                "show_yoga": False, "yoga_tip": "", "yoga_gif": ""
            })

    # 2. Mood Logic
    score, label = 5, "Neutral"
    if any(w in msg_lower for w in ["sad", "cry", "lonely"]): score, label = 2, "Sad"
    elif any(w in msg_lower for w in ["happy", "excited"]): score, label = 8, "Happy"
    elif any(w in msg_lower for w in ["angry", "mad"]): score, label = 1, "Angry"
    elif any(w in msg_lower for w in ["stress", "anxious"]): score, label = 3, "Stressed"

    # 3. Yoga Check
    if any(w in msg_lower for w in ["pain", "neck", "back", "tired"]):
        show_yoga = True
        label = "Physical Pain"
        key = "neck" if "neck" in msg_lower else "back" if "back" in msg_lower else "stress" if "stress" in msg_lower else "tired"
        yoga_tip, yoga_gif = YOGA_SOLUTIONS[key]["tip"], YOGA_SOLUTIONS[key]["gif"]

    # 4. Stress Ask (Only if NOT venting)
    if ("stress" in msg_lower or "anxious" in msg_lower) and not is_venting:
        session['waiting_for_breathing'] = True
        if uid and not is_venting: db_helper.add_mood(uid, score, label, user_message)
        return jsonify({
            "reply": "You seem stressed. Want to do a breathing exercise?", 
            "show_breathing": False,
            "show_yoga": False, "yoga_tip": "", "yoga_gif": ""
        })

    # 5. DB SAVE (Skip if Venting)
    if uid and not is_venting:
        db_helper.add_mood(uid, score, label, user_message)
    else:
        print(" Venting Mode On: Message NOT saved.")

    # 6. Gemini Call
    if API_KEY:
        try:
            system_prompt = "User is venting. Just listen and be supportive. Reply in 2 sentences." if is_venting else f"User said: {user_message}. You are a therapist. Reply in 2 sentences."
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
            payload = {"contents": [{"parts": [{"text": system_prompt + f" User input: {user_message}"}]}]}
            res = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
            if res.status_code == 200: reply = res.json()['candidates'][0]['content']['parts'][0]['text']
        except: pass

    # 🔥 FIX: Ab 'show_yoga' guarantee defined hai
    return jsonify({
        "reply": reply, 
        "show_breathing": False, 
        "show_yoga": show_yoga, 
        "yoga_tip": yoga_tip, 
        "yoga_gif": yoga_gif
    })

if __name__ == '__main__':
    app.run(debug=True)