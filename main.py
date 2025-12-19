from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, InlineQueryHandler, MessageHandler, filters, CallbackContext
from config import TOKEN
from handlers import start,help, ask,  button,handle_group_message, handle_selection,select_language,set_language,whois
from manageadmin import (
    admin_conversation,  # Import admin management conversation
)
from manageusers import (
    user_conversation,
    )  # Import user management conversation


if __name__ == '__main__':
    # Create the Application and pass it your bot's token
    app = Application.builder().token(TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", start))

    # Register handlers for button callbacks
    app.add_handler(CallbackQueryHandler(button))

    # Add admin management conversation handler
    app.add_handler(admin_conversation)  # Use the conversation handler for admin management

    # Add user management conversation handler
    app.add_handler(user_conversation)  # Use the conversation handler for user management

    #other main commands the ask stands for the emahoy yelebe function
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("ask", ask))
    app.add_handler(CommandHandler("whois", whois))
    
    # Register handlers for group messages and photo messages
    app.add_handler(MessageHandler(filters.REPLY & filters.ChatType.GROUPS, handle_group_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_selection))
    app.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, ask))  # To handle photos sent with /ask

    # Register language selection handlers
    app.add_handler(CallbackQueryHandler(select_language, pattern='^language$'))
    app.add_handler(CallbackQueryHandler(set_language, pattern='^language_.*'))

    
    #for the excel and the manual user enter choice 

    app.run_polling()
