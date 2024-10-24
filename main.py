from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext
from config import TOKEN
from handlers import start, help, ask, button, select_category, handle_group_message, handle_selection, handle_courses, select_college, select_department,select_division, select_year, select_semester

if __name__ == '__main__':
    # Create the Application and pass it your bot's token
    app = Application.builder().token(TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("ask", ask))

    # Register handlers for button callbacks
    app.add_handler(CallbackQueryHandler(button))

    # Register the handler for the course selection (main button to trigger courses)
    app.add_handler(CallbackQueryHandler(handle_courses, pattern='^courses$'))

    # Register handlers for group messages and photo messages
    app.add_handler(MessageHandler(filters.REPLY & filters.ChatType.GROUPS, handle_group_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_selection))
    app.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, ask))  # To handle photos sent with /ask


    # Register the handler for selecting a college
    app.add_handler(CallbackQueryHandler(select_college, pattern='^college_'))

    # Register the handler for selecting a department
    app.add_handler(CallbackQueryHandler(select_department, pattern='^department_'))

    # Register the handler for selecting a division
    app.add_handler(CallbackQueryHandler(select_division, pattern='^division_'))

    # Register the handler for selecting a year
    app.add_handler(CallbackQueryHandler(select_year, pattern='^year_'))

    # Register the handler for selecting a semester
    app.add_handler(CallbackQueryHandler(select_semester, pattern='^semester_'))

    # Start the Bot
    app.run_polling()

