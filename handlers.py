# main_bot_script.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from utils import generate_identifier, user_questions
from config import EDUCATIONAL_GROUP_ID, SPIRITUAL_GROUP_ID, SOCIAL_GROUP_ID, BOT_USERNAME
# In handlers.py
from course_handling import (
    handle_courses, 
    select_college, 
    select_department, 
    select_division,
    select_year, 
    select_semester, 
    handle_course_selection,  # Import the new function
    COURSES
)

async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("📚 Courses", callback_data='courses')],
        [InlineKeyboardButton("👥 About Us", callback_data='about')],
        [InlineKeyboardButton("❓ Questions/Advice", callback_data='questions')],
        [InlineKeyboardButton("🌐 Language", callback_data='language')],
        [InlineKeyboardButton("🔍 Course Search", callback_data='search')],
        [InlineKeyboardButton("🆘 Help Desk", callback_data='help')],
         [InlineKeyboardButton("🛒 SUQ (Shop)", web_app={"url": "https://shoptelegram.vercel.app/"})]  # Add the shop option here
   
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Hello! I am Emahoy app. Please select an option:", reply_markup=reply_markup)

async def select_category(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'questions':
        category_keyboard = [
            [InlineKeyboardButton("📚 Educational", callback_data='educational')],
            [InlineKeyboardButton("🙏 Spiritual", callback_data='spiritual')],
            [InlineKeyboardButton("👥 Social", callback_data='social')],
        ]
        reply_markup = InlineKeyboardMarkup(category_keyboard)
        await query.edit_message_text("Please select a category:", reply_markup=reply_markup)

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'courses':
        await handle_courses(update, context)
    elif query.data.startswith('college_'):
        await select_college(update, context)  # Handle college selection
    elif query.data.startswith('department_'):
        await select_department(update, context)  # Handle department selection
    elif query.data.startswith('division_'):
        await select_division(update, context)
    elif query.data.startswith('year_'):
        await select_year(update, context)  # Handle year selection
    elif query.data.startswith('semester_'):
        await select_semester(update, context)  # Handle semester selection
    elif query.data.startswith('course_'):
        await handle_course_selection(update, context)  # Handle course selection
    elif query.data == 'about':
        await query.edit_message_text("About the bot: This bot provides information about courses and more.")
    elif query.data == 'questions':
        await select_category(update, context)
    elif query.data == 'language':
        await query.edit_message_text("You can customize the bot language in the settings section.")
    elif query.data == 'search':
        await query.edit_message_text("To search for a course, type @ASTU_COBOT and the course you want to search.")
    elif query.data == 'help':
        await query.edit_message_text("Help: This section provides assistance with using the bot.")


    elif query.data == 'shop':  # Handle the SUQ(Shop) button
        shop_url = "https://shoptelegram.vercel.app/"  # Replace with your shop URL
        keyboard = [[InlineKeyboardButton("Open Shop", url=shop_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Click the button below to visit the shop:", reply_markup=reply_markup)


    elif query.data in ['educational', 'spiritual', 'social']:
        context.user_data['selected'] = query.data
        await query.edit_message_text(f"You've selected {query.data.capitalize()}. Type /ask followed by your question.")

async def help(update: Update, context: CallbackContext) -> None:
    message = "Hello, I am Emahoy app. Please tell me what I can help you with?\n\n"
    message += "1. Educational\n"
    message += "2. Spiritual\n"
    message += "3. Social"
    await update.message.reply_text(message)

async def handle_selection(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text.strip()

    if user_input == '1':
        context.user_data['selected'] = 'educational'
        await update.message.reply_text("You've selected Educational. Type /ask followed by your question.")
    elif user_input == '2':
        context.user_data['selected'] = 'spiritual'
        await update.message.reply_text("You've selected Spiritual. Type /ask followed by your question.")
    elif user_input == '3':
        context.user_data['selected'] = 'social'
        await update.message.reply_text("You've selected Social. Type /ask followed by your question.")
    else:
        await update.message.reply_text("Invalid input. Please type 1 for Educational, 2 for Spiritual, or 3 for Social.")

async def ask(update: Update, context: CallbackContext) -> None:
    selected_category = context.user_data.get('selected')

    if not selected_category:
        await update.message.reply_text("Please select a category first by typing 1 for Educational, 2 for Spiritual, or 3 for Social.")
        return

    if update.message.photo:
        caption = update.message.caption if update.message.caption else ""
        identifier = generate_identifier()
        user_questions[update.effective_user.id] = {'category': selected_category, 'question': caption, 'identifier': identifier}
        group_id = {
            'educational': EDUCATIONAL_GROUP_ID,
            'spiritual': SPIRITUAL_GROUP_ID,
            'social': SOCIAL_GROUP_ID,
        }[selected_category]
        photo_id = update.message.photo[-1].file_id
        await context.bot.send_photo(chat_id=group_id, photo=photo_id, caption=f"**Question ID: {identifier}**\nQuestion from {update.effective_user.username}: {caption}")
        await update.message.reply_text("We have recieved your question . we will get back to you soon.")
    else:
        question = ' '.join(context.args) if context.args else ""
        if not question:
            await update.message.reply_text("Please ask a question after typing /ask or send a photo with a caption.")
            return

        identifier = generate_identifier()
        user_questions[update.effective_user.id] = {'category': selected_category, 'question': question, 'identifier': identifier}

        group_id = {
            'educational': EDUCATIONAL_GROUP_ID,
            'spiritual': SPIRITUAL_GROUP_ID,
            'social': SOCIAL_GROUP_ID,
        }[selected_category]

        await context.bot.send_message(chat_id=group_id, text=f"**Question ID: {identifier}**\nQuestion from {update.effective_user.username}: {question}")
        await update.message.reply_text("We have recieved your question . we will get back to you soon.")

async def handle_group_message(update: Update, context: CallbackContext) -> None:
    # Check if the message is from a group
    if update.message.chat.type in ['group', 'supergroup']:
        # Ignore the message if the bot is not mentioned
        if BOT_USERNAME not in (update.message.text or update.message.caption or ""):
            return

    # Now, we can handle replies to questions
    if update.message.reply_to_message:
        reply_message = update.message.reply_to_message
        original_message = reply_message.caption if reply_message.caption else reply_message.text if reply_message.text else ""

        if 'Question ID:' in original_message:
            try:
                identifier_part = original_message.split('Question ID:')[1].split('\n')[0].strip()
                identifier = identifier_part.split('**')[0].strip()
                user_id = None
                for uid, info in user_questions.items():
                    if info['identifier'] == identifier:
                        user_id = uid
                        break

                if user_id:
                    # Check if the response is an image
                    if update.message.photo:
                        photo_id = update.message.photo[-1].file_id
                        caption = update.message.caption if update.message.caption else f"Answer from EmaHoy-Yelebe for Question ID: {identifier}"
                        await context.bot.send_photo(chat_id=user_id, photo=photo_id, caption=caption)
                    else:
                        response = update.message.text if update.message.text else ""
                        response_lines = response.split('\n')
                        response_cleaned = '\n'.join(line for line in response_lines if 'Question ID:' not in line).strip()
                        await context.bot.send_message(chat_id=user_id, text=f"Answer from EmaHoy-Yelebe: {response_cleaned}")

                    # Notify in the group chat that a response has been sent
                    await context.bot.send_message(chat_id=update.message.chat.id, text=f"Response to Question ID {identifier} has been sent to {update.message.from_user.username}.")
                else:
                    await context.bot.send_message(chat_id=update.message.chat.id, text="Error: Unable to find the question with that identifier.")
            except Exception as e:
                await context.bot.send_message(chat_id=update.message.chat.id, text=f"Error processing your response: {str(e)}")
        else:
            await context.bot.send_message(chat_id=update.message.chat.id, text="Error: Invalid message format. Please reply to the question message.")
    
    # Handle normal text messages
    elif update.message.text:
        # If the bot is mentioned in a normal message
        if BOT_USERNAME in update.message.text:
            await handle_selection(update, context)
        else:
            # Ignore normal messages that don't mention the bot
            return

    # Handle photo messages
    elif update.message.photo:
        if BOT_USERNAME in (update.message.caption or ""):
            await handle_selection(update, context)


