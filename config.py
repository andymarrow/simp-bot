# config.py
import firebase_admin
from firebase_admin import credentials, db

TOKEN = 'YOUR_BOT_TOKEN_HERE'

try:
    # This reads the key from the file instead of hardcoding it in the script
    cred = credentials.Certificate("emahoyyelbebot-firebase-adminsdk-x5v6p-62a7923ee6.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://emahoyyelbebot-default-rtdb.firebaseio.com/'
    })
    firebase_db = db
except Exception as e:
    print(f"Error: {e}")