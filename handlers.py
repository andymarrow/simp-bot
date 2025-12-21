# handlers.py
import hashlib
import logging
import time
import asyncio # Required for the waiting logic
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import CallbackContext

# Import helper functions from the fixed utils.py
from utils import (
    generate_identifier, 
    generate_anonymous_id, 
    save_active_question, 
    get_question_mapping
)
from config import firebase_db, EDUCATIONAL_GROUP_ID, SPIRITUAL_GROUP_ID, SOCIAL_GROUP_ID, SUPERADMIN_USER


BOT_USERNAME = "@Ema_Hoy_Yelebe_bots"

HASH_SALT = "GEBI_GUBAE_SECRET_SALT"

# Temporary cache to handle multiple images (albums)
# Format: {media_group_id: timestamp}
AUTHORIZED_ALBUMS = {}

# New cache to collect images before sending them as a group
# Format: { media_group_id: {"user_id": int, "media": [], "chat_id": int, "anon_id": str} }
ALBUM_COLLECTOR = {}


class LanguageManager:
    def __init__(self):
        self.language = "language"

    def set_user_language(self, telegram_username, language_choice):
        data = {
            "telegram_username": telegram_username,
            "language": language_choice,
        }
        firebase_db.reference(self.language).child(telegram_username).set(data)

    def get_user_language(self, telegram_username):
        user_language_ref = firebase_db.reference(self.language).child(telegram_username)
        user_data = user_language_ref.get()
        if user_data and 'language' in user_data:
            return user_data['language']
        else:
            return "english"

# --- HELPER FUNCTIONS ---

def get_anon_id(telegram_id):
    """Generates a consistent 8-character ID based on the user's numeric ID."""
    raw_str = f"{telegram_id}{HASH_SALT}"
    hash_obj = hashlib.sha256(raw_str.encode())
    return f"STU-{hash_obj.hexdigest()[:8].upper()}"

async def send_collected_album(context: CallbackContext, mg_id: str):
    """Background task that waits for all parts of an album and sends them as one media group."""
    # Wait a moment for all parts of the album to arrive from Telegram servers
    await asyncio.sleep(2.0) 
    
    if mg_id in ALBUM_COLLECTOR:
        data = ALBUM_COLLECTOR.pop(mg_id)
        try:
            if not data["media"]:
                return

            # Telegram displays the caption of the FIRST media item in the group.
            # We ensure the header is placed correctly in our collection logic.
            await context.bot.send_media_group(
                chat_id=data["user_id"],
                media=data["media"]
            )
            
            # Notify the expert group once that the whole album was sent
            await context.bot.send_message(
                chat_id=data["chat_id"],
                text=f"✅ Full album response sent to student `{data['anon_id']}`"
            )
        except Exception as e:
            logging.error(f"Failed to send collected album: {e}")

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

# --- HANDLERS ---


async def start(update: Update, context: CallbackContext) -> None:
    context.user_data.clear()
    user = update.message.from_user
    user_username = user.username if user.username else str(user.id)
    
    # --- RESTORED AUTHORIZATION LOGIC (Commented out as requested) ---
    # user_ref = firebase_db.reference('users')
    # user_data = user_ref.order_by_child('telegram_username').equal_to(f"@{user_username}").get()
    # if not user_data:
    #     await update.message.reply_text("You are not allowed to use this bot.")
    #     return
    # --------------------------------------------------------------

    if user_username:
        # We lowercase the key for consistency, but save the display username as a field
        anon_id = generate_anonymous_id(user.id)
        firebase_db.reference('users').child(user_username.lower()).update({
            "telegram_id": user.id,
            "anonymous_id": anon_id,
            "telegram_username": user_username # This ensures /whois finds the name
        })

    admin_ref = firebase_db.reference('admins')
    admin_data = admin_ref.order_by_child('telegram_username').equal_to(f"@{user_username}").get()
    is_admin = bool(admin_data)
    is_super_admin = user_username in SUPERADMIN_USER

    course_manager = LanguageManager()
    user_language = course_manager.get_user_language(user_username)

    if user_language == 'amharic':
        message = "እንኳን ደህና መጡ! ምን ማድረግ ይፈልጋሉ?"
        options = [
            [InlineKeyboardButton("❓ ጥያቄ/ምክር", callback_data='questions')],
            [InlineKeyboardButton("🌐 ቋንቋ", callback_data='language')],
            [InlineKeyboardButton("👥 ስለ እኛ", callback_data='about')],
            [InlineKeyboardButton("🆘 የእርዳታ ጠቅላላ መድረክ", callback_data='help')],
        ]
        manage_admins_label = "⚙️ አስተዳዳሪዎችን አስተዳድር"
        manage_users_label = "⚙️ ተጠቃሚዎችን አስተዳድር"
    else:
        message = "Hello! I am Emahoy app. Please select an option:"
        options = [
            [InlineKeyboardButton("❓ Questions/Advice", callback_data='questions')],
            [InlineKeyboardButton("🌐 Language", callback_data='language')],
            [InlineKeyboardButton("👥 About Us", callback_data='about')],
            [InlineKeyboardButton("🆘 Help Desk", callback_data='help')],
        ]
        manage_admins_label = "⚙️ Manage Admins"
        manage_users_label = "⚙️ Manage Users"

    if is_super_admin:
        options.append([InlineKeyboardButton(manage_users_label, callback_data='manage_Users')])
        options.append([InlineKeyboardButton(manage_admins_label, callback_data='manage_Admins')])
    elif is_admin:
        options.append([InlineKeyboardButton(manage_users_label, callback_data='manage_Users')])

    reply_markup = InlineKeyboardMarkup(options)
    await update.message.reply_text(message, reply_markup=reply_markup)

# Callback query handler for back button
async def handle_back_button(update: Update, context: CallbackContext) -> None:
    """Handles the back button and navigates to the start."""
    query = update.callback_query
    await query.answer()

    # Navigate back to the start menu
    await start(update, context)

async def manage_admins(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    # Get the username of the user who clicked the button from the callback query
    user_username = query.from_user.username if query.from_user else None  

    # Get the user's language preference from Firebase
    language_manager = LanguageManager()
    user_language = language_manager.get_user_language(user_username)

    # Update the message to include instructions for managing admins
    if user_language == 'amharic':
        await query.edit_message_text("አድሚን ይጨምሩ፣ /add_admin ይጻፉ።\n"
                                       "አድሚን ይለቀቁ፣ /remove_admin ይጻፉ።\n"
                                       "አድሚን ሊስት፣ /list_admin ይጻፉ.\n"
                                       "ወደ ቀደም ተመለስ ይጻፉ ወይም /back ይጻፉ።")
    else:
        await query.edit_message_text("To add an admin, type or click /add_admin.\n"
                                       "To remove an admin, type or click /remove_admin.\n"
                                       "To list the current admins, type or click /list_admin.\n"
                                       "To go back, type or click /back.")
        
async def manage_users(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

     # Get the username of the user who clicked the button from the callback query
    user_username = query.from_user.username if query.from_user else None  

    # Get the user's language preference from Firebase
    language_manager = LanguageManager()
    user_language = language_manager.get_user_language(user_username)

    # Update the message to include instructions for managing users
    if user_language == 'amharic':
        await query.edit_message_text("አባል ይጨምሩ፣ /add_user ይጻፉ።\n"
                                       "አባል ይለቀቁ፣ /remove_user ይጻፉ።\n"
                                       "አባል ሊስት፣ /list_user ይጻፉ።\n"
                                       "ወደ ቀደም ተመለስ ይጻፉ ወይም /back ይጻፉ።")
    else:
        await query.edit_message_text("To add a user, type or click /add_user.\n"
                                       "To remove a user, type or click /remove_user.\n"
                                       "To list the current users, type or click /list_user.\n"
                                       "To go back, type or click /back.")
    
async def select_language(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    user_username = query.from_user.username  # Get the username of the user

    # Check if the user has already selected a language from Firebase
    language_manager = LanguageManager()
    user_language = language_manager.get_user_language(user_username)

    # Default to Amharic if no language is set
    if not user_language:
        user_language = 'amharic'
        # Optionally, store the default Amharic selection in Firebase for first-time users
        language_manager.set_user_language(user_username, user_language)

    # Language selection options
    language_keyboard = [
        [InlineKeyboardButton("Amharic", callback_data='language_amharic')],
        [InlineKeyboardButton("English", callback_data='language_english')],
    ]
    reply_markup = InlineKeyboardMarkup(language_keyboard)

    # Display the language selection message in the user's current or default language
    if user_language == 'amharic':
        await query.edit_message_text("እባኮትን ቋንቋዎን ይምረጡ:", reply_markup=reply_markup)  # Amharic version
    else:
        await query.edit_message_text("Please choose your preferred language:", reply_markup=reply_markup)

async def set_language(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_username = query.from_user.username

    # Determine the selected language based on callback data
    if query.data == 'language_amharic':
        language_choice = 'amharic'
    elif query.data == 'language_english':
        language_choice = 'english'

    # Store the language preference in Firebase
    language_manager = LanguageManager()
    language_manager.set_user_language(user_username, language_choice)

    # Confirm the language choice to the user
    await query.edit_message_text(f"Language set to {language_choice.capitalize()}.")



async def select_category(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    user_username = query.from_user.username if query.from_user else None  
    
    # Get the user's language preference from Firebase
    language_manager = LanguageManager()
    user_language = language_manager.get_user_language(user_username)

    if query.data == 'questions':
        if user_language == 'amharic':
            category_keyboard = [
                [InlineKeyboardButton("📚 ትምህርታዊ", callback_data='educational')],  # Educational
                [InlineKeyboardButton("🙏 እምነታዊ", callback_data='spiritual')],  # Spiritual
                [InlineKeyboardButton("👥 ማህበራዊ", callback_data='social')],  # Social
            ]
            await query.edit_message_text("እባክዎ አንዱን ይምረጡ፡፡", reply_markup=InlineKeyboardMarkup(category_keyboard))  # Please select a category
        else:
            category_keyboard = [
                [InlineKeyboardButton("📚 Educational", callback_data='educational')],
                [InlineKeyboardButton("🙏 Spiritual", callback_data='spiritual')],
                [InlineKeyboardButton("👥 Social", callback_data='social')],
            ]
            await query.edit_message_text("Please select a category:", reply_markup=InlineKeyboardMarkup(category_keyboard))


async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    # Get the username of the user who clicked the button from the callback query
    user_username = query.from_user.username if query.from_user else None  

    # Get the user's language preference from Firebase
    language_manager = LanguageManager()
    user_language = language_manager.get_user_language(user_username)

    if query.data == 'manage_Admins':
        await manage_admins(update, context)
    elif query.data == 'manage_Users':  # Handle Manage Users button
        await manage_users(update, context)
    elif query.data == 'add_admin':
        await add_admin(update, context)  # Call the add_admin function
    elif query.data == 'remove_admin':
        await remove_admin(update, context)  # Call the remove_admin function
    elif query.data == 'add_user':
        await add_user(update, context)  # Call the add_user function
    elif query.data == 'remove_user':
        await remove_user(update, context)  # Call the remove_user function
    
    elif query.data == 'back_to_start':
        await start(update, context)  # Go back to the start      
    elif query.data == 'about':
        # Determine the selected language based on user preference
        if user_language == 'amharic':
            await query.edit_message_text(
                "📖 *በተመለከተው ቦት እንደዚህ ነው*: ይህ ቦት በሚሄረታብ ሳምሰን በአዳማ ሳይንስ እና ቴክኖሎጂ ዩኒቨርሲቲ ገቢ ጉባኤ አሰራር ቡድን ተሰራ። "
                "👨‍💻 ቡድኑ በድር ጣቢያዎች፣ መተግበሪያዎች፣ ቦቶች እና ሌሎችም እንደ እቅዶች በእንቅስቃሴ ላይ ያሉት ተማሪዎችን ይያዛል። "
                "📱 ከሰሪው እንዲገናኙ በ ቴሌግራም @andymarrow ይደርሱ።"
            )
        else:
            await query.edit_message_text(
                "📖 *About this bot*: This bot was created by Miheretab Samson from the development team of Adama Science and Technology University Gebi Gubae. "
                "👨‍💻 The team consists of students collaborating on various projects like websites, applications, bots, and more. "
                "📱 To contact the developer, reach out on Telegram at @andymarrow."
            )
    elif query.data == 'questions':
        await select_category(update, context)
    elif query.data == 'language':
        await query.edit_message_text("You can customize the bot language in the settings section.")
    elif query.data == 'help':
        if user_language == 'amharic':
            await query.edit_message_text(
                "📖እንደዚህ ነው"
              )
        else :
            await query.edit_message_text(
            "🎉 **Welcome to Emahoy Yelebe Bot** 🎉\n\n"
            "🤖 **Emahoy App** is a versatile and interactive Telegram bot designed to assist users with **educational** 📚, **spiritual** ✨, and **social inquiries** 🤝.\n\n"
            "Whether you’re seeking knowledge on academic subjects 📖, looking for spiritual guidance 🙏, or needing help with life skills 🌱, Emahoy is here to help! 🚀\n\n"
            "Here’s how you can use the bot:\n\n"
            "1️⃣ **Spiritual Guidance** ✨: \n"
            "Click on the **Spiritual** section and type `/ask` followed by your question to receive spiritual advice and guidance on your inquiries.\n\n"
            "2️⃣ **Educational Support** 📚: \n"
            "Choose the **Educational** section, then type `/ask` and your question. You can ask about subjects you’re studying, and our team is always ready to assist with your academic journey.\n\n"
            "3️⃣ **Social Skills** 🤝: \n"
            "Select the **Social** section and use the `/ask` command to inquire about life skills and personal development. Our dedicated team is here to help with any questions you may have.\n\n"
            "Feel free to explore and ask your questions! We’re always here to support you. 💪"
        )
    elif query.data in ['educational', 'spiritual', 'social']:
        context.user_data['selected'] = query.data
        await query.edit_message_text(f"You've selected {query.data.capitalize()}. Type /ask followed by your question.")
    if query.data == 'language':
        await select_language(update, context)
    elif query.data.startswith('language_'):
        await set_language(update, context)

async def help(update: Update, context: CallbackContext) -> None:
    message = "Hello, I am Emahoy app. Please tell me what I can help you with?\n\n"
    message += "1. Educational\n"
    message += "2. Spiritual\n"
    message += "3. Social"
    await update.message.reply_text(message)

async def handle_selection(update: Update, context: CallbackContext) -> None:
    
    user_input = update.message.text.strip()

    user_username = update.message.from_user.username  # Get the username of the user  
      
    
    # Get the user's language preference from Firebase
    language_manager = LanguageManager()
    user_language = language_manager.get_user_language(user_username)

    if user_input == '1':
        context.user_data['selected'] = 'educational'
        if user_language == 'amharic':
            await update.message.reply_text("ትምህርታዊ መርጠዋል፡፡ እባክዎ ጥያቄዎን /ask ካሉ በኋላ ይጻፉ.")  # You've selected Educational. Type /ask followed by your question.
        else:
            await update.message.reply_text("You've selected Educational. Type /ask followed by your question.")
    elif user_input == '2':
        context.user_data['selected'] = 'spiritual'
        if user_language == 'amharic':
            await update.message.reply_text("እምነታዊ መርጠዋል፡፡ እባክዎ ጥያቄዎን /ask ካሉ በኋላ ይጻፉ.")  # You've selected Spiritual. Type /ask followed by your question.
        else:
            await update.message.reply_text("You've selected Spiritual. Type /ask followed by your question.")
    elif user_input == '3':
        context.user_data['selected'] = 'social'
        if user_language == 'amharic':
            await update.message.reply_text("ማህበራዊ መርጠዋል፡፡ እባክዎ ጥያቄዎን /ask ካሉ በኋላ ይጻፉ.")  # You've selected Social. Type /ask followed by your question.
        else:
            await update.message.reply_text("You've selected Social. Type /ask followed by your question.")
    else:
        if update.message.chat.type not in ['group', 'supergroup']:
            if user_language == 'amharic':
                await update.message.reply_text("የተሳሳተ ግብረ መልስ፡፡ እባክዎ 1 ለትምህርታዊ፣ 2 ለእምነታዊ፣ 3 ለማህበራዊ ይጻፉ.")  # Invalid input. Please type 1 for Educational, 2 for Spiritual, or 3 for Social.
            else:
                await update.message.reply_text("Invalid input. Please type 1 for Educational, 2 for Spiritual, or 3 for Social.")

async def ask(update: Update, context: CallbackContext) -> None:
    selected_category = context.user_data.get('selected')
    user = update.effective_user
    user_username = user.username if user.username else str(user.id)
    
    lang_manager = LanguageManager()
    user_language = lang_manager.get_user_language(user.username)

    if not selected_category:
        msg = "እባክዎ መጀመሪያ አይነት ይምረጡ" if user_language == 'amharic' else "Please select a category first."
        await update.message.reply_text(msg)
        return

    identifier = generate_identifier()
    anon_id = generate_anonymous_id(user.id)
    save_active_question(identifier, user.id, anon_id, selected_category)

    # Silent Auto-Registration check: Ensure user is in DB when they ask
    firebase_db.reference('users').child(user_username.lower()).update({
        "telegram_id": user.id,
        "anonymous_id": anon_id,
        "telegram_username": user_username
    })

    group_id = {
        'educational': EDUCATIONAL_GROUP_ID,
        'spiritual': SPIRITUAL_GROUP_ID,
        'social': SOCIAL_GROUP_ID,
    }[selected_category]

    question_text = (update.message.caption if update.message.photo else ' '.join(context.args)) or ""
    
    if not question_text and not update.message.photo:
        await update.message.reply_text("Please provide a question.")
        return

    forward_header = (
        f"📩 New Inquiry\n"
        f"Question ID: {identifier}\n"
        f"From Student: {anon_id}\n"
        f"Category: {selected_category.capitalize()}\n"
        f"--------------------------\n"
    )

    if update.message.photo:
        await context.bot.send_photo(chat_id=group_id, photo=update.message.photo[-1].file_id, caption=f"{forward_header}Question: {question_text}", parse_mode='Markdown')
    else:
        await context.bot.send_message(chat_id=group_id, text=f"{forward_header}Question: {question_text}", parse_mode='Markdown')

    await update.message.reply_text("ጥያቄዎ ተልኳል! / Your question has been sent.")

async def handle_group_message(update: Update, context: CallbackContext) -> None:
    if update.message.chat.type not in ['group', 'supergroup']:
        return

    msg_text = update.message.text or update.message.caption or ""
    mg_id = update.message.media_group_id
    
    # 1. Authorization Check (Handling multiple images in an album)
    is_authorized = False
    if BOT_USERNAME in msg_text:
        is_authorized = True
        if mg_id:
            AUTHORIZED_ALBUMS[mg_id] = time.time()
    elif mg_id and mg_id in AUTHORIZED_ALBUMS:
        if time.time() - AUTHORIZED_ALBUMS[mg_id] < 60:
            is_authorized = True

    if not is_authorized or not update.message.reply_to_message:
        return

    reply_to = update.message.reply_to_message
    original_msg = reply_to.caption or reply_to.text or ""

    if 'Question ID:' in original_msg:
        try:
            identifier = original_msg.split('Question ID:')[1].split('\n')[0].strip().replace('`', '').replace('*', '')
            mapping = get_question_mapping(identifier)

            if mapping:
                target_user_id = mapping['user_id']
                clean_text = msg_text.replace(BOT_USERNAME, "").strip()
                header = "✅ **Answer from EmaHoy-Yelebe:**\n\n" if BOT_USERNAME in msg_text else ""

                if mg_id:
                    # Collect album parts
                    if mg_id not in ALBUM_COLLECTOR:
                        ALBUM_COLLECTOR[mg_id] = {
                            "user_id": target_user_id, 
                            "media": [], 
                            "chat_id": update.message.chat.id,
                            "anon_id": mapping['anon_id']
                        }
                        asyncio.create_task(send_collected_album(context, mg_id))
                    
                    # Add current photo to the list as an InputMediaPhoto object
                    ALBUM_COLLECTOR[mg_id]["media"].append(
                        InputMediaPhoto(
                            media=update.message.photo[-1].file_id, 
                            caption=header + clean_text if (header or clean_text) else None,
                            parse_mode='Markdown'
                        )
                    )
                else:
                    # Handle single message (Text or Photo)
                    if update.message.photo:
                        await context.bot.send_photo(chat_id=target_user_id, photo=update.message.photo[-1].file_id, caption=header + clean_text, parse_mode='Markdown')
                    else:
                        await context.bot.send_message(chat_id=target_user_id, text=header + clean_text, parse_mode='Markdown')
                    
                    await update.message.reply_text(f"✅ Response sent to student `{mapping['anon_id']}`")
        except Exception as e:
            logging.error(f"Group reply error: {e}")

# --- SUPER ADMIN ONLY COMMAND ---

async def whois(update: Update, context: CallbackContext) -> None:
    if update.message.chat.type != 'private': return
    user_username = update.message.from_user.username
    if user_username not in SUPERADMIN_USER:
        await update.message.reply_text("⛔ Access Denied.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /whois STU-XXXX")
        return

    target_id = context.args[0].upper()
    users_ref = firebase_db.reference('users').get()

    if not users_ref:
        await update.message.reply_text("❌ No users found in database.")
        return

    found_user = None
    db_key = None
    for uname, data in users_ref.items():
        if data.get('anonymous_id') == target_id:
            found_user = data
            db_key = uname
            break

    if found_user:
        # If fields are missing (not registered by Admin), show "Not Provided" instead of "None"
        name = found_user.get('name', 'Not Provided')
        # If telegram_username field is missing, fallback to the database key
        username = found_user.get('telegram_username', db_key)
        phone = found_user.get('phone', 'Not Provided')
        year = found_user.get('year', 'Not Provided')

        info = (
            f"🔍 Identity Revealed\n"
            f"ID: {target_id}\n"
            f"Name: {name}\n"
            f"Username: @{username}\n"
            f"Phone: {phone}\n"
            f"Year: {year}"
        )
        await update.message.reply_text(info, parse_mode='Markdown')
    else:
        await update.message.reply_text(f"❌ No user found with ID {target_id}.")