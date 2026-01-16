import os
import json
import warnings
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from pymongo import MongoClient
import google.generativeai as genai
from dotenv import load_dotenv

# 1. Suppress warnings
warnings.filterwarnings("ignore")

# 2. Load Environment Variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "hackathon_key")

# 3. Setup MongoDB (With Safe Fallback)
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
try:
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
    db = client['serene_db']
    moods_collection = db['moods']
    # Test connection
    client.server_info()
    print("[OK] MongoDB Connected Successfully")
except Exception as e:
    print("[WARNING] MongoDB NOT Connected (Running in Offline Mode)")
    moods_collection = None

# 4. Setup Gemini AI
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("[ERROR] GEMINI_API_KEY is missing in .env file!")
else:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

# --- ROUTES ---

@app.route('/')
def home():
    if 'user_id' not in session:
        session['user_id'] = os.urandom(4).hex()
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get('message')
        if not user_message:
            return jsonify({"reply": "Please type something."})

        # Simple Prompt Engineering
        prompt = f"""
        You are Serene, a compassionate mental health companion. 
        The user says: "{user_message}".
        Reply empathetically in 2-3 sentences.
        """

        # Generate AI Response
        response = model.generate_content(prompt)
        ai_reply = response.text.strip()

        # Save to Database (if active)
        if moods_collection:
            try:
                moods_collection.insert_one({
                    "user_id": session.get('user_id'),
                    "message": user_message,
                    "reply": ai_reply,
                    "date": datetime.utcnow()
                })
            except:
                pass 

        return jsonify({"reply": ai_reply})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"reply": "I'm having trouble connecting right now."})

@app.route('/dashboard-data')
def dashboard_data():
    if not moods_collection:
        return jsonify([
            {"date": "2025-01-01", "score": 5},
            {"date": "2025-01-02", "score": 7}
        ])
    
    try:
        user_id = session.get('user_id')
        data = list(moods_collection.find({"user_id": user_id}).limit(10))
        return jsonify([{"date": "Today", "score": 8}]) 
    except:
        return jsonify([])

if __name__ == '__main__':
    app.run(debug=True)