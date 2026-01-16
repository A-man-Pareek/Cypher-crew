import pymongo
from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

class Database:
    _instance = None

    def __new__(cls):
        # Singleton Pattern: Taaki baar-bar connection na banana pade
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            
            # LOCAL CONNECTION
            try:
                # Agar MongoDB localhost par chal raha hai
                cls._instance.client = MongoClient("mongodb://localhost:27017/")
                # Connection Test
                cls._instance.client.admin.command('ping')
                print(" Database Connected Successfully!")
            except Exception as e:
                print(f" Database Connection Error: {e}")
                
            # Database aur Collections (Tables) set karna
            cls._instance.db = cls._instance.client.mental_health_bot
            cls._instance.users = cls._instance.db.users
            cls._instance.mood_logs = cls._instance.db.mood_logs
            
            # Indexing (Fast search ke liye)
            cls._instance.users.create_index([("username", ASCENDING)], unique=True)
            cls._instance.mood_logs.create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)])
            
        return cls._instance

    # --- 1. USER LOGIN / SIGNUP ---
    def create_user(self, username, password):
        try:
            # Password ko encrypt karke save karenge (Security ke liye)
            hashed_password = generate_password_hash(password)
            user_id = self.users.insert_one({
                "username": username,
                "password": hashed_password,
                "created_at": datetime.now()
            }).inserted_id
            return str(user_id)
        except pymongo.errors.DuplicateKeyError:
            return None # Username pehle se kisi ne le liya hai

    def verify_user(self, username, password):
        user = self.users.find_one({"username": username})
        # Check karega ki password sahi hai ya nahi
        if user and check_password_hash(user['password'], password):
            return user
        return None

    # --- 2. MOOD TRACKING ---
# --- 2. MOOD TRACKING (Updated: Ab kabhi reject nahi karega) ---
    def add_mood(self, user_id, mood_score, emotion_label, note):
        # Fix: Agar User ID kharab hai, toh nayi bana lo par data SAVE karo!
        try:
            if not user_id or not ObjectId.is_valid(str(user_id)):
                # Agar ID valid nahi hai, toh ek nayi temporary ID bana do
                valid_user_id = ObjectId()
            else:
                # Agar sahi hai toh wahi use karo
                valid_user_id = ObjectId(user_id)
        except Exception:
            valid_user_id = ObjectId()

        log = {
            "user_id": valid_user_id,
            "mood_score": mood_score,
            "emotion_label": emotion_label,
            "note": note,
            "timestamp": datetime.now()
        }
        
        # Save to Database
        self.mood_logs.insert_one(log)
        
    def get_dashboard_data(self, user_id, limit=30):
        if not ObjectId.is_valid(user_id):
            return []
            
        cursor = self.mood_logs.find(
            {"user_id": ObjectId(user_id)},
            {"mood_score": 1, "timestamp": 1, "emotion_label": 1, "_id": 0}
        ).sort("timestamp", DESCENDING).limit(limit)
        return list(cursor)[::-1]

    # --- 3. DATA CLEANUP ---
    def delete_data(self, user_id, scope):
        if not ObjectId.is_valid(user_id):
            return "Invalid User ID"

        if scope == 'all':
            result = self.mood_logs.delete_many({"user_id": ObjectId(user_id)})
            return f"Deleted {result.deleted_count} records."
        elif scope == 'today':
            start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            result = self.mood_logs.delete_many({
                "user_id": ObjectId(user_id),
                "timestamp": {"$gte": start_of_day}
            })
            return f"Deleted {result.deleted_count} records from today."

# Initialize (Is variable ko hum app.py mein import karenge)
db_helper = Database()