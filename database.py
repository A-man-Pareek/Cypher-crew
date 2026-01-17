import pymongo
from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            try:
                cls._instance.client = MongoClient("mongodb://localhost:27017/")
                cls._instance.client.admin.command('ping')
                print(" Database Connected Successfully!")
            except Exception as e:
                print(f" Database Connection Error: {e}")
                
            cls._instance.db = cls._instance.client.mental_health_bot
            cls._instance.users = cls._instance.db.users
            cls._instance.mood_logs = cls._instance.db.mood_logs
            
            cls._instance.users.create_index([("username", ASCENDING)], unique=True)
            cls._instance.mood_logs.create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)])
            
        return cls._instance

    def create_user(self, username, password):
        try:
            hashed_password = generate_password_hash(password)
            user_id = self.users.insert_one({
                "username": username,
                "password": hashed_password,
                "created_at": datetime.now()
            }).inserted_id
            return str(user_id)
        except pymongo.errors.DuplicateKeyError:
            return None 

    def verify_user(self, username, password):
        user = self.users.find_one({"username": username})
        if user and check_password_hash(user['password'], password):
            return user
        return None

    def add_mood(self, user_id, mood_score, emotion_label, message):
        try:
            if not user_id or not ObjectId.is_valid(str(user_id)):
                valid_user_id = ObjectId()
            else:
                valid_user_id = ObjectId(user_id)
        except Exception:
            valid_user_id = ObjectId()

        log = {
            "user_id": valid_user_id,
            "mood_score": mood_score,
            "emotion_label": emotion_label,  # DB me 'emotion_label' hi rahega
            "message": message,
            "timestamp": datetime.now()
        }
        self.mood_logs.insert_one(log)

    # --- CHAT RESTORE FIX ---
   # --- CHAT RESTORE FIX (JSON ID ERROR SOLVED) ---
    def get_chat_history(self, user_id):
        try:
            if not ObjectId.is_valid(user_id):
                return []
            
            # 1. Fetch data from MongoDB
            history = list(self.mood_logs.find({"user_id": ObjectId(user_id)}).sort("timestamp", -1).limit(20))
            
            cleaned_history = []
            for chat in history:
                # 2. 🔥 Sabse Zaroori Step: ObjectId ko String banao
                chat_id_str = str(chat['_id'])
                
                # 3. Data clean karo (Handle missing keys)
                chat_data = {
                    "_id": chat_id_str, # String format mein ID
                    "message": chat.get('message', chat.get('note', '')),
                    # Agar 'emotion' save hai toh wo lo, nahi toh 'emotion_label' check karo
                    "emotion": chat.get('emotion', chat.get('emotion_label', 'Neutral')),
                    "timestamp": chat['timestamp'].strftime("%Y-%m-%d %H:%M")
                }
                
                # 4. Clean list mein daalo
                cleaned_history.append(chat_data)
                
            return cleaned_history

        except Exception as e:
            print(f"Error fetching history: {e}")
            return []

    # --- INSIGHTS FIX ---
    def get_user_insights(self, user_id):
        try:
            if not ObjectId.is_valid(user_id):
                return None

            logs = list(self.mood_logs.find({"user_id": ObjectId(user_id)}).sort("timestamp", 1))

            if not logs:
                return None

            # Keys must match script2.js (Capitalized)
            counts = {"Happy": 0, "Sad": 0, "Anxious": 0, "Neutral": 0, "Angry": 0, "Stressed": 0}
            
            recent_logs = logs[-7:] 
            chart_labels = []
            chart_data = []

            last_log = logs[-1]
            today_score = last_log.get("mood_score", 5)
            today_label = last_log.get("emotion_label", "Neutral").capitalize()

            for log in logs:
                # 🔥 FIX: Lowercase ko Capitalize karo (sad -> Sad) taaki graph match kare
                raw_emotion = log.get("emotion_label", "Neutral")
                emotion = raw_emotion.capitalize() if raw_emotion else "Neutral"
                
                # Handle Synonyms
                if "Stress" in emotion: emotion = "Stressed"
                if "Tired" in emotion: emotion = "Neutral" # Map tired to neutral or add category

                if emotion in counts:
                    counts[emotion] += 1
                else:
                    counts["Neutral"] += 1

            for log in recent_logs:
                day_name = log["timestamp"].strftime("%a")
                chart_labels.append(day_name)
                chart_data.append(log.get("mood_score", 5))

            return {
                "current_mood": today_label,
                "current_score": today_score,
                "counts": counts,
                "trend_labels": chart_labels,
                "trend_data": chart_data
            }

        except Exception as e:
            print(f"Error getting insights: {e}")
            return None
# --- DELETE HISTORY FUNCTION ---
    def delete_chat_history(self, user_id):
        try:
            if not ObjectId.is_valid(user_id):
                return False
            
            # User ke saare mood logs delete kar do
            result = self.mood_logs.delete_many({"user_id": ObjectId(user_id)})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting history: {e}")
            return False
        
db_helper = Database()