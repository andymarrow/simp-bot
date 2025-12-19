# utils.py
import random
import hashlib
import logging
from config import HASH_SALT, firebase_db

# This is the function your handlers.py was missing
def generate_identifier():
    """Generates a random 4-digit ID for a specific question."""
    return str(random.randint(1000, 9999))

def generate_anonymous_id(telegram_id):
    """Generates a consistent STU-XXXX ID based on the user's numeric Telegram ID."""
    raw_str = f"{telegram_id}{HASH_SALT}"
    hash_obj = hashlib.sha256(raw_str.encode())
    return f"STU-{hash_obj.hexdigest()[:8].upper()}"

def save_active_question(identifier, user_id, anon_id, category):
    """Saves the mapping to Firebase so the bot remembers the user after restart."""
    ref = firebase_db.reference('active_questions')
    ref.child(identifier).set({
        'user_id': user_id,
        'anon_id': anon_id,
        'category': category
    })

def get_question_mapping(identifier):
    """Retrieves the user who asked a specific question."""
    return firebase_db.reference('active_questions').child(identifier).get()