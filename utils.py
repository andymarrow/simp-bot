import random

user_questions = {} # {user_id: {'category': str, 'question': str, 'identifier': str, 'responses': list}}

def generate_identifier():
    return str(random.randint(1000, 9999))
