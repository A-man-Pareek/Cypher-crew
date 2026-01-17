import os
import requests
import json
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from dotenv import load_dotenv
from database import db_helper 

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "super_secret_key_change_me")

# API Key Check
raw_key = os.getenv("GEMINI_API_KEY")
API_KEY = raw_key.strip() if raw_key else None

YOGA_SOLUTIONS = {
    "neck": {"tip": "Neck Rolls", "gif": "/static/neck.gif"},
    "back": {"tip": "Child Pose", "gif": "/static/back.gif"},
    "tired": {"tip": "Side Stretch", "gif": "/static/tired.gif"},
    "stress": {"tip": "Shoulder Roll", "gif": "/static/stress.gif"}
}

# --- ROUTES ---
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

@app.route('/insight')
def insight_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('insight.html')

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
    try:
        history = db_helper.get_chat_history(session['user_id'])
        return jsonify({"success": True, "history": history})
    except Exception as e:
        print(f"History Error: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/chat_api', methods=['POST'])
def chat_api():
    data = request.json
    user_message = data.get('message', '')
    is_venting = data.get('is_venting', False)

    if not user_message: return jsonify({"reply": "Please type something."})
    
    uid = session.get('user_id')
    reply = "I am listening."
    detected_emotion = "Neutral"
    mood_score = 5

    # 1. BREATHING CHECK
    if session.get('waiting_for_breathing'):
        session.pop('waiting_for_breathing')
        if any(w in user_message.lower() for w in ["yes", "ok", "sure", "do it"]):
            return jsonify({"reply": "Starting breathing exercise...", "show_breathing": True, "emotion": "Calm"})

    # 2. GEMINI AI ANALYSIS (RE-IMPLEMENTED 2.5 LOGIC)
    if API_KEY:
        try:
            # System Instruction for strict JSON
            system_instruction = """
            You are Serene, a compassionate mental health AI. 
            Identify the dominant emotion and reply.
            Return STRICTLY VALID JSON:
            {
                "reply": "Your response here (max 2 sentences)",
                "emotion": "One of: Happy, Sad, Angry, Anxious, Neutral, Tired, Stressed"
            }
            """
            if is_venting:
                system_instruction += " Note: User is venting. Be supportive and listen."

            # Experimental models usually work best on v1beta
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
            
            payload = {
                "contents": [{"parts": [{"text": f"{system_instruction}\nUser: {user_message}"}]}]
            }
            
            res = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=12)
            
            if res.status_code == 200:
                result_text = res.json()['candidates'][0]['content']['parts'][0]['text']
                # Clean Markdown
                clean_text = result_text.replace("```json", "").replace("```", "").strip()
                ai_data = json.loads(clean_text)
                reply = ai_data.get("reply", "I am here for you.")
                detected_emotion = ai_data.get("emotion", "Neutral")
            else:
                print(f"[ERROR] API returned status: {res.status_code}")
                # FALLBACK to local logic so the UI doesn't break
                msg_low = user_message.lower()
                if any(w in msg_low for w in ["sad", "cry", "lonely"]): detected_emotion = "Sad"
                elif any(w in msg_low for w in ["happy", "good"]): detected_emotion = "Happy"

        except Exception as e:
            print(f"[DEBUG] AI Logic Error: {e}")

    # 3. MAPPING
    emotion_map = {"Happy": 8, "Excited": 9, "Sad": 2, "Angry": 1, "Anxious": 4, "Neutral": 5, "Stressed": 3}
    mood_score = emotion_map.get(detected_emotion, 5)

    # 4. YOGA CHECK
    show_yoga = False
    yoga_tip, yoga_gif = "", ""
    if any(w in user_message.lower() for w in ["pain", "neck", "back", "tired"]):
        show_yoga = True
        key = "neck" if "neck" in user_message.lower() else "back" if "back" in user_message.lower() else "tired"
        if key in YOGA_SOLUTIONS:
            yoga_tip, yoga_gif = YOGA_SOLUTIONS[key]["tip"], YOGA_SOLUTIONS[key]["gif"]

    # 5. DB SAVE
    if uid and not is_venting:
        db_helper.add_mood(uid, mood_score, detected_emotion, user_message)

    return jsonify({
        "reply": reply,
        "emotion": detected_emotion,
        "show_breathing": False,
        "show_yoga": show_yoga,
        "yoga_tip": yoga_tip,
        "yoga_gif": yoga_gif
    })

@app.route('/delete_history_api', methods=['POST'])
def delete_history_api():
    if 'user_id' not in session: return jsonify({"success": False})
    success = db_helper.delete_chat_history(session['user_id'])
    return jsonify({"success": success})

if __name__ == '__main__':
    app.run(debug=True)