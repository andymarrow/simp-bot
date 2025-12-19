import logging
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, filters, Updater, CallbackContext
from config import TOKEN, firebase_db

# Define states for the admin management conversation
(
    ADD_ADMIN_NAME,
    ADD_ADMIN_FAMILY_MEMBER,
    ADD_ADMIN_PHONE,
    ADD_ADMIN_TELEGRAM_USERNAME,
    ADD_ADMIN_YEAR,
    REMOVE_ADMIN_NAME,
    REMOVE_ADMIN_TELEGRAM_USERNAME 
) = range(7)

# Class to manage admins (you can extend this class to include Firebase logic if needed)
class AdminManager:
    def __init__(self):
        self.admins = "admins"  # Firebase collection name

    def add_admin(self, name, family_member, phone, telegram_username, year):
        data = {
            "name": name,
            "family_member": family_member,
            "phone": phone,
            "telegram_username": telegram_username,
            "year": year
        }
        firebase_db.reference(self.admins).child(telegram_username).set(data)
    # Add this method to remove an admin
    def remove_admin(self, name, telegram_username):
        admin_ref = firebase_db.reference(self.admins)
        admin_data = admin_ref.order_by_child('telegram_username').equal_to(telegram_username).get()
        
        if admin_data:
            for admin_key in admin_data:
                if admin_data[admin_key]['name'] == name:
                    admin_ref.child(admin_key).delete()
                    return True
        return False
    
# Entry point for adding admin
async def initiate_add_admin(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Please send the name of the admin.")
    return ADD_ADMIN_NAME

# Process adding admin details
async def process_add_admin_name(update: Update, context: CallbackContext) -> int:
    context.user_data['admin_name'] = update.message.text
    await update.message.reply_text("Now, please enter the family member (father/mother):")
    return ADD_ADMIN_FAMILY_MEMBER

async def process_add_admin_family_member(update: Update, context: CallbackContext) -> int:
    context.user_data['admin_family_member'] = update.message.text
    await update.message.reply_text("Please enter the phone number:")
    return ADD_ADMIN_PHONE

async def process_add_admin_phone(update: Update, context: CallbackContext) -> int:
    context.user_data['admin_phone'] = update.message.text
    await update.message.reply_text("Please enter the Telegram username:")
    return ADD_ADMIN_TELEGRAM_USERNAME

async def process_add_admin_telegram_username(update: Update, context: CallbackContext) -> int:
    context.user_data['admin_telegram_username'] = update.message.text
    await update.message.reply_text("Finally, please enter the year of college:")
    return ADD_ADMIN_YEAR

async def process_add_admin_year(update: Update, context: CallbackContext) -> int:
    year = update.message.text
    # Create an instance of AdminManager to add the admin
    admin_manager = AdminManager()
    admin_manager.add_admin(
        context.user_data['admin_name'],
        context.user_data['admin_family_member'],
        context.user_data['admin_phone'],
        context.user_data['admin_telegram_username'],
        year
    )
    await update.message.reply_text(f"Admin {context.user_data['admin_name']} has been added successfully!")
    context.user_data.clear()  # Clear user data
    return ConversationHandler.END

# Function to list all admins
async def list_admins(update: Update, context: CallbackContext) -> None:
    admin_ref = firebase_db.reference('admins')
    admin_data = admin_ref.get()

    if not admin_data:
        await update.message.reply_text("No admins found.")
        return

    # Prepare a table-like text output for the list of admins
    admin_list = "Admins List:\n\n"
    admin_list += "{:<15} {:<10} {:<15} {:<20} {:<10}\n".format("Name", "Family", "Phone", "Telegram", "Year")
    admin_list += "-" * 70 + "\n"

    for key, admin in admin_data.items():
        admin_list += "{:<15} {:<10} {:<15} {:<20} {:<10}\n".format(
            admin.get('name', 'N/A'),
            admin.get('family_member', 'N/A'),
            admin.get('phone', 'N/A'),
            admin.get('telegram_username', 'N/A'),
            admin.get('year', 'N/A')
        )

    await update.message.reply_text(f"```{admin_list}```", parse_mode='Markdown')



# Entry point for removing admin
async def initiate_remove_admin(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Please send the name of the admin to remove.")
    return REMOVE_ADMIN_NAME

# Process admin name input
async def process_remove_admin_name(update: Update, context: CallbackContext) -> int:
    context.user_data['remove_admin_name'] = update.message.text
    await update.message.reply_text("Now, please enter the Telegram username of the admin.")
    return REMOVE_ADMIN_TELEGRAM_USERNAME

# Process Telegram username input and remove admin
async def process_remove_admin_telegram_username(update: Update, context: CallbackContext) -> int:
    telegram_username = update.message.text
    admin_manager = AdminManager()
    removed = admin_manager.remove_admin(context.user_data['remove_admin_name'], telegram_username)
    
    if removed:
        await update.message.reply_text(f"Admin {context.user_data['remove_admin_name']} has been removed successfully!")
    else:
        await update.message.reply_text("No matching admin found. Please check the name and Telegram username.")
    
    context.user_data.clear()  # Clear user data
    return ConversationHandler.END


# Fallback to cancel the operation
async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Operation canceled.")
    context.user_data.clear()
    return ConversationHandler.END

# Unknown message handler
async def unknown_message(update: Update, context: CallbackContext):
    await update.message.reply_text("I didn't understand that. Please send a valid command.")

# Define the ConversationHandler for admin management
admin_conversation = ConversationHandler(
    entry_points=[
        CommandHandler("add_admin", initiate_add_admin),
        CommandHandler("remove_admin", initiate_remove_admin),
        CommandHandler("list_admin", list_admins),
        ],
    states={
        ADD_ADMIN_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_add_admin_name)],
        ADD_ADMIN_FAMILY_MEMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_add_admin_family_member)],
        ADD_ADMIN_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_add_admin_phone)],
        ADD_ADMIN_TELEGRAM_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_add_admin_telegram_username)],
        ADD_ADMIN_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_add_admin_year)],
        REMOVE_ADMIN_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_remove_admin_name)],
        REMOVE_ADMIN_TELEGRAM_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_remove_admin_telegram_username)],
    },
    fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.ALL, unknown_message)],
    allow_reentry=True  # Allow re-entering the conversation

)

# You may also want to export these functions
def add_admin(update: Update, context: CallbackContext):
    # Call the function that starts the conversation
    return initiate_add_admin(update, context)

def remove_admin(update: Update, context: CallbackContext):
    # Call the function that starts the conversation
    return initiate_remove_admin(update, context)

# Main function to run the bot
if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Add admin management conversation handler
    dispatcher.add_handler(admin_conversation)

    # Add other command handlers (e.g., start command)
    dispatcher.add_handler(CommandHandler('start', lambda update, context: update.message.reply_text("Welcome!")))

    updater.start_polling()
    updater.idle()
