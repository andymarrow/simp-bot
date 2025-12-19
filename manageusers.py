import os
import json
import pandas as pd
import logging
from telegram import InlineKeyboardButton,InlineKeyboardMarkup,Update
from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, filters, Updater, CallbackContext
from AI.Excelfileaccepting import handle_file_upload
from config import TOKEN, firebase_db
from firebase_admin import db  # Ensure you have this import
from utils import generate_anonymous_id

# Define states for user management conversation
(
    ADD_USER_NAME,
    ADD_USER_FAMILY_MEMBER,
    ADD_USER_PHONE,
    ADD_USER_TELEGRAM_USERNAME,
    ADD_USER_YEAR,
    REMOVE_USER_NAME,
    EXCEL_FILE_UPLOAD,
    REMOVE_USER_TELEGRAM_USERNAME 
) = range(8)


class LanguageManager:
    def __init__(self):
        self.language = "language"  # Firebase reference for languages

    def set_user_language(self, telegram_username, language_choice):
        # Store user's language preference in Firebase
        data = {
            "telegram_username": telegram_username,
            "language": language_choice,
        }
        firebase_db.reference(self.language).child(telegram_username).set(data)

    def get_user_language(self, telegram_username):
    # Retrieve the user's language preference from Firebase
        user_language_ref = firebase_db.reference(self.language).child(telegram_username)
        user_data = user_language_ref.get()

        if user_data and 'language' in user_data:
            logging.info(f"User language found: {user_data['language']}")
            return user_data['language']
        else:
            logging.info("No language preference found, defaulting to English.")
            return "english"  # Default to English if no language preference is set

# Class to manage users (you can extend this class to include Firebase logic if needed)
class UserManager:
    def __init__(self):
        self.users = "users"  # Firebase collection name

    def add_user(self, name, family_member, phone, telegram_username, year):
        # We don't have the numeric ID yet if adding manually by username, 
        # so we will generate/save the ID when the user first interacts with the bot.
        # However, for now, let's store the data we have.
        data = {
            "name": name,
            "family_member": family_member,
            "phone": phone,
            "telegram_username": telegram_username.replace("@", ""),
            "year": year,
            # anonymous_id will be updated the first time they click /start
        }
        firebase_db.reference(self.users).child(telegram_username.replace("@", "")).set(data)
        
    # Add this method to remove a user
    def remove_user(self, name, telegram_username):
        user_ref = firebase_db.reference(self.users)
        user_data = user_ref.order_by_child('telegram_username').equal_to(telegram_username).get()
        
        if user_data:
            for user_key in user_data:
                if user_data[user_key]['name'] == name:
                    user_ref.child(user_key).delete()
                    return True
        return False

# Start the process of adding a user
async def initiate_add_user(update: Update, context: CallbackContext):
    context.user_data.clear()  # Clear previous user data
    context.user_data['materials'] = []  # Initialize materials list

    await update.message.reply_text("How would you like to add the user? Use /manual to enter manually or /excel to upload an Excel file.")


    
async def process_excel_with_gemini(file_path):
    # Read the Excel file using pandas
    df = pd.read_excel(file_path)

    # Convert the DataFrame to a list of dictionaries
    extracted_data = df.to_dict(orient='records')

    # i can do additional processing here if necessary
    return extracted_data  

async def process_add_File_upload(update: Update, context: CallbackContext):
    user_username = update.message.from_user.username  # Get the username of the user  
    
    # Language handling
    language_manager = LanguageManager()
    user_language = language_manager.get_user_language(update.message.from_user.username)
    
    if user_language == 'amharic':
        await update.message.reply_text("እባክዎ የኮርስ ፋይል ይላኩ:")
    else:
        await update.message.reply_text("Please upload the excel file to be inserted to the DB:")
    
    return EXCEL_FILE_UPLOAD
  

async def process_excel_file_upload(update: Update, context: CallbackContext):
    file_path = None  # Initialize file_path to None

    try:
        # Capture the file ID from Telegram
        file_id = update.message.document.file_id
        new_file = await context.bot.get_file(file_id)

        # Download the file to a local path (temporarily)
        file_path = f"{file_id}.xlsx"
        await new_file.download_to_drive(file_path)

        # Call handle_file_upload from your Gemini integration
        extracted_data = handle_file_upload(file_path)  # Process with Gemini

        # If successful, parse the extracted data
        if extracted_data:
            try:
                # Wrap the extracted JSON objects into a list
                extracted_data = f"[{extracted_data}]"

                # Convert the JSON string into a list of dictionaries
                extracted_data = json.loads(extracted_data)  # Parse the string to JSON

                # Create a reference to the Firebase database
                users_ref = firebase_db.reference('users')  # Access the 'users' reference

                # Upload each entry to Firebase
                for entry in extracted_data:
                    family_member = entry.get('family_member')
                    name = entry.get('name')
                    phone = entry.get('phone')
                    telegram_username = entry.get('telegram_username')
                    year = entry.get('year')

                    # Upload data to Firebase
                    users_ref.push({
                        "family_member": family_member,
                        "name": name,
                        "phone": phone,
                        "telegram_username": telegram_username,
                        "year": year
                    })

                await update.message.reply_text("Family member data has been successfully added to Firebase.")
            except json.JSONDecodeError:
                await update.message.reply_text("Failed to parse the extracted data as JSON.")
        else:
            await update.message.reply_text("Failed to process the Excel file. No data extracted.")

    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")

    finally:
        # Clean up the temporary file if it was created
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

    return ConversationHandler.END

async def initiate_ask_to_add_user(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Please send the name of the user.")
    return ADD_USER_NAME

# Process adding user details
async def process_add_user_name(update: Update, context: CallbackContext) -> int:
    user_username = update.message.from_user.username  # Get the username of the user  
    
    
    # Get the user's language preference from Firebase
    language_manager = LanguageManager()
    user_language = language_manager.get_user_language(user_username)
    
    
    context.user_data['user_name'] = update.message.text
    
    if user_language == 'amharic':
        await update.message.reply_text("አሁን እባክዎ የቤተሰብ አባል ይምረጡ (አባ/እናት):")  # Now, please enter the family member (father/mother):
    else:
        await update.message.reply_text("Now, please enter the family member (father/mother):")
    
    return ADD_USER_FAMILY_MEMBER

async def process_add_user_family_member(update: Update, context: CallbackContext) -> int:
    user_username = update.message.from_user.username  # Get the username of the user  
    
    
    # Get the user's language preference from Firebase
    language_manager = LanguageManager()
    user_language = language_manager.get_user_language(user_username)
    
    context.user_data['user_family_member'] = update.message.text
    
    if user_language == 'amharic':
        await update.message.reply_text("እባክዎ የስልኩን ቁጥር ይላኩ።")  # Please enter the phone number:
    else:
        await update.message.reply_text("Please enter the phone number:")
    
    return ADD_USER_PHONE

async def process_add_user_phone(update: Update, context: CallbackContext) -> int:
    user_username = update.message.from_user.username  # Get the username of the user  
    
    
    # Get the user's language preference from Firebase
    language_manager = LanguageManager()
    user_language = language_manager.get_user_language(user_username)
    
    context.user_data['user_phone'] = update.message.text
    
    if user_language == 'amharic':
        await update.message.reply_text("እባክዎ የቴሌግራም የተጠቃሚ ስም ይላኩ።")  # Please enter the Telegram username:
    else:
        await update.message.reply_text("Please enter the Telegram username:")
    
    return ADD_USER_TELEGRAM_USERNAME

async def process_add_user_telegram_username(update: Update, context: CallbackContext) -> int:
    user_username = update.message.from_user.username  # Get the username of the user  
    
    
    # Get the user's language preference from Firebase
    language_manager = LanguageManager()
    user_language = language_manager.get_user_language(user_username)
    
    context.user_data['user_telegram_username'] = update.message.text
    
    if user_language == 'amharic':
        await update.message.reply_text("አሁን እባክዎ የኮሌጅ ዓመት ይላኩ።")  # Finally, please enter the year of college:
    else:
        await update.message.reply_text("Finally, please enter the year of college:")
    
    return ADD_USER_YEAR

async def process_add_user_year(update: Update, context: CallbackContext) -> int:
    user_username = update.message.from_user.username  # Get the username of the user  
    
    
    # Get the user's language preference from Firebase
    language_manager = LanguageManager()
    user_language = language_manager.get_user_language(user_username)
    
    year = update.message.text
    # Create an instance of UserManager to add the user
    user_manager = UserManager()
    user_manager.add_user(
        context.user_data['user_name'],
        context.user_data['user_family_member'],
        context.user_data['user_phone'],
        context.user_data['user_telegram_username'],
        year
    )
    
    if user_language == 'amharic':
        await update.message.reply_text(f"የተጠቃሚ ስም {context.user_data['user_name']} በትክክል ተጨምሯል!")  # User has been added successfully!
    else:
        await update.message.reply_text(f"User {context.user_data['user_name']} has been added successfully!")
    
    context.user_data.clear()  # Clear user data
    return ConversationHandler.END


# Entry point for removing user
async def initiate_remove_user(update: Update, context: CallbackContext) -> int:
    user_username = update.message.from_user.username  # Get the username of the user  
    
    
    # Get the user's language preference from Firebase
    language_manager = LanguageManager()
    user_language = language_manager.get_user_language(user_username)
    
    if user_language == 'amharic':
        await update.message.reply_text("እባክዎ የሚሰርዝ የተጠቃሚ ስም ይላኩ።")  # Please send the name of the user to remove.
    else:
        await update.message.reply_text("Please send the name of the user to remove.")
    
    return REMOVE_USER_NAME

# Process user name input
async def process_remove_user_name(update: Update, context: CallbackContext) -> int:
    user_username = update.message.from_user.username  # Get the username of the user  
    
    
    # Get the user's language preference from Firebase
    language_manager = LanguageManager()
    user_language = language_manager.get_user_language(user_username)
    
    context.user_data['remove_user_name'] = update.message.text
    
    if user_language == 'amharic':
        await update.message.reply_text("አሁን የተጠቃሚውን የቴሌግራም የተጠቃሚ ስም ይላኩ።")  # Now, please enter the Telegram username of the user.
    else:
        await update.message.reply_text("Now, please enter the Telegram username of the user.")
    
    return REMOVE_USER_TELEGRAM_USERNAME

# Process Telegram username input and remove user
async def process_remove_user_telegram_username(update: Update, context: CallbackContext) -> int:
    user_username = update.message.from_user.username  # Get the username of the user  
    
    
    # Get the user's language preference from Firebase
    language_manager = LanguageManager()
    user_language = language_manager.get_user_language(user_username)
    
    telegram_username = update.message.text
    user_manager = UserManager()
    removed = user_manager.remove_user(context.user_data['remove_user_name'], telegram_username)
    
    if removed:
        if user_language == 'amharic':
            await update.message.reply_text(f"የተጠቃሚ ስም {context.user_data['remove_user_name']} በትክክል ተሰርዟል!")  # User has been removed successfully!
        else:
            await update.message.reply_text(f"User {context.user_data['remove_user_name']} has been removed successfully!")
    else:
        if user_language == 'amharic':
            await update.message.reply_text("ምርጥ የተጠቃሚ ስም አልተገኝም። እባክዎ ስም እና የቴሌግራም የተጠቃሚ ስም በትክክል ያስገቡ።")  # No matching user found. Please check the name and Telegram username.
        else:
            await update.message.reply_text("No matching user found. Please check the name and Telegram username.")
    
    context.user_data.clear()  # Clear user data
    return ConversationHandler.END

async def list_users(update: Update, context: CallbackContext) -> None:
    # Get the user's language preference
    user_username = update.message.from_user.username if update.message else None
    language_manager = LanguageManager()
    user_language = language_manager.get_user_language(user_username)

    # Create a reference to the users collection in Firebase
    users_ref = firebase_db.reference('users')
    user_data = users_ref.get()

    if not user_data:
        # No users found message based on language
        if user_language == 'amharic':
            await update.message.reply_text("ምንም አባል አልተመዘገበም።")
        else:
            await update.message.reply_text("No users are registered.")
        return

    # Prepare a table-like text output for the list of users
    if user_language == 'amharic':
        user_list = "የተመዘገቡ አባላት:\n\n"
        user_list += "{:<15} {:<10} {:<15} {:<20} {:<10}\n".format("ስም", "አባል", "ስልክ", "ቴሌግራም የተጠቃሚ", "አመት")
    else:
        user_list = "Registered Users:\n\n"
        user_list += "{:<15} {:<10} {:<15} {:<20} {:<10}\n".format("Name", "Family", "Phone", "Telegram", "Year")

    user_list += "-" * 70 + "\n"

    # Populate the table with user data
    for user_key, user_info in user_data.items():
        if user_language == 'amharic':
            user_list += "{:<15} {:<10} {:<15} {:<20} {:<10}\n".format(
                user_info.get('name', 'አልተገኘም'),
                user_info.get('family_member', 'አልተገኘም'),
                user_info.get('phone', 'አልተገኘም'),
                user_info.get('telegram_username', 'አልተገኘም'),
                user_info.get('year', 'አልተገኘም')
            )
        else:
            user_list += "{:<15} {:<10} {:<15} {:<20} {:<10}\n".format(
                user_info.get('name', 'N/A'),
                user_info.get('family_member', 'N/A'),
                user_info.get('phone', 'N/A'),
                user_info.get('telegram_username', 'N/A'),
                user_info.get('year', 'N/A')
            )

    # Send the formatted table to the chat
    await update.message.reply_text(f"```{user_list}```", parse_mode='Markdown')



# Fallback to cancel the operation
async def cancel(update: Update, context: CallbackContext) -> int:
    user_username = update.message.from_user.username  # Get the username of the user  
    
    
    # Get the user's language preference from Firebase
    language_manager = LanguageManager()
    user_language = language_manager.get_user_language(user_username)
    
    if user_language == 'amharic':
        await update.message.reply_text("እንደዚህ ያለው እንቅስቃሴ ተሰርዟል።")  # Operation canceled.
    else:
        await update.message.reply_text("Operation canceled.")

    context.user_data.clear()
    return ConversationHandler.END

# Unknown message handler
async def unknown_message(update: Update, context: CallbackContext):
    user_username = update.message.from_user.username  # Get the username of the user  
    
    
    # Get the user's language preference from Firebase
    language_manager = LanguageManager()
    user_language = language_manager.get_user_language(user_username)
    
    if user_language == 'amharic':
        await update.message.reply_text("ይህ የላኩት ትእዛዝ አይታወቅም። እባክዎ ታዋቂ ትእዛዝ ይላኩ።")  # I didn't understand that. Please send a valid command.
    else:
        await update.message.reply_text("I didn't understand that. Please send a valid command.")


# Define the ConversationHandler for user management
user_conversation = ConversationHandler(
    entry_points=[
        CommandHandler("add_user", initiate_add_user),
        CommandHandler("manual", initiate_ask_to_add_user),
        CommandHandler("excel", process_add_File_upload),
        CommandHandler("remove_user", initiate_remove_user),
        CommandHandler("list_user", list_users),
    ],
    states={
        ADD_USER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_add_user_name)],
        ADD_USER_FAMILY_MEMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_add_user_family_member)],
        ADD_USER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_add_user_phone)],
        ADD_USER_TELEGRAM_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_add_user_telegram_username)],
        ADD_USER_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_add_user_year)],
        REMOVE_USER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_remove_user_name)],
        EXCEL_FILE_UPLOAD: [MessageHandler(filters.Document.ALL, process_excel_file_upload)],
        REMOVE_USER_TELEGRAM_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_remove_user_telegram_username)],
    },
    fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.ALL, unknown_message)],
    allow_reentry=True  # Allow re-entering the conversation

)

# You may also want to export these functions
def add_user(update: Update, context: CallbackContext):
    # Call the function that starts the conversation
    return initiate_add_user(update, context)

def remove_user(update: Update, context: CallbackContext):
    # Call the function that starts the conversation
    return initiate_remove_user(update, context)

# Main function to run the bot
if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Add user management conversation handler
    dispatcher.add_handler(user_conversation)
    # dispatcher.add_handler(CommandHandler('manual', initiate_ask_to_add_user))
    # dispatcher.add_handler(CommandHandler('excel', process_excel_file_upload))

    # Add other command handlers (e.g., start command)
    dispatcher.add_handler(CommandHandler('start', lambda update, context: update.message.reply_text("Welcome!")))

    updater.start_polling()
    updater.idle()
