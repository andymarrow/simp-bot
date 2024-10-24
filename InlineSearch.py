import re
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import CallbackContext, Updater, CommandHandler, InlineQueryHandler
from telegram import Update
from uuid import uuid4  # This is used for generating unique IDs


# Sample course list
course_list = [
["Applied Mathematics I", "Math1101",
     ],
    ["General Physics-I", "Phys1101",
     ],
    ["General Chemistry", "Chem1101",
     ],
    ["Introduction to Computing", "CSE1101",
     ],
    ["Communicative English Skills", "ENG1011",
     ],
    ["Civic and Ethical Education", "LAR1011",
     ],
    ["Health &Physical Education I", "HPEd1011",
     ],
    ["Logic and Critical Thinking", "LAR1012",
     ],
    ["Applied Mathematics II", "Math1102",
     ],
    ["Emerging Technologies", "Phys1102",
     ],
    ["Fundamentals of Programming", "CSE1102",
     ],
    ["Engineering Drawing", "DME1102",
     ],
    ["Basic Writing Skills", "ENG1102",
     ],
    ['Data Structure and Algorithm', 'CSE2101',
     ],
    ['Electronic Circuit', 'ECE2101'],
    ['Applied Mathematics III', 'MATH2051',
     ],
    ['Fundamental of Electrical Engineering', 'PCE2101',
     ],
    ['Principle of Economics', 'SOS311'],
    ['Object Oriented Programming', 'CSE2202',
     ],
    ['Discrete Mathematics for CSE', 'CSE2206',
     ],
    ['Digital Logic Design', 'ECE3204'],
    ['Database Systems', 'CSE3207'],
    ['Electronic circuit II', 'ECE2202'],
    ['System Programming', 'CSE2320'],
    ['Computer Graphics', 'CSE3310'],
    ['Algorithms', 'CSE3211'],
    ['Probability and Random Process', 'ECE3103',
     ],
    ['Fund. of software Engineering', 'CSE3205',
     ],
    ['Computer Architecture & Organization', 'CSE3203',
     ],
    ['Operating System', 'CSE3204'],
    ['Data Communication & Computer Networks', 'CSE3221',
     ],
    ['Introduction to Artificial', 'CSE3206',
     ],
    ['SOftware Requirement Engineering', 'CSE3308',
     ],
    ['Web Programming', 'CSE3306'],
    ['Advanced Programming', 'CSE3312'],
    ['Formal Language and automata Theory', 'unknown',
     ],
    ['Engineering Research and Development Methodology', 'CSE4221',
     ],
    ['Multimedia Tech.', 'CSE4303'],
    ['Software Design and Architecture', 'CSE4309',
     ],
    ['Mobile Computing and Applications', 'CSE4311',
     ],
    ['Signals and Systems', 'ECE2204'],
    ['Introduction to Data mining', 'CSE5317',
     ],
    ['Introduction to NLP', 'CSE5321'],
    ['Computer System and security', 'Unkown',
     ],
    ['Programming languages', 'CSE4202'],
    ['Project Management', 'CSE4302'],
    ['Introduction to Law', 'Unknown'],
    ['Compiler Design', 'CSE4310'],
    ['Digital Signal Processing', 'ECE3205',
     ],
    ['VLSI Design', 'ECE5307'],
    ['Electrical Network Analysis and synthesis', 'PCE3201',
     ],
    ['Introduction to Computer Vision', 'CSE4312',
     ],
    ['Semester Project', 'CSE5201'],
    ['Seminar', 'CSE5205'],
    ['Distributed Systems', 'CSE5307'],
    ['Wireless mobile Networks', 'CSE5309',
     ],
    ['Image Processing', 'CSE5311'],
    ['Human Computer Interaction', 'CSE5313',
     ],
    ['Introduction to Audio & Video Production', 'CSE5315',
     ],
    ['Advanced Network', 'CSE5319'],
    ['Introduction to Control Systems', 'PCE3204',
     ],
    ['B.Sc. Project', 'CSE5202'],
    ['Entrepreneurship for Engineers', 'SOSC412', ],
    ['Computer Games & Animation', 'CSE5304',
     ],
    ['Special Topics in Computer Science & Engineering', 'CSE5306',
     ],
    ['Real time and Embedded Systems', 'CSE5308',
     ],
    ['Software Quality & Testing', 'CSE5310',
     ],
    ['Computer Ethics and Social Issues', 'CSE5312',
     ],
    ['Introduction to Robotics and Industrial Automation', 'PCE5308',
     ]

]




# Function to handle inline search queries
async def inline_query(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query.lower()

    # If no query is provided, respond with a prompt
    if not query:
        result = InlineQueryResultArticle(
            id=str(uuid4()),
            title="Start Typing course name or course code",
            description="No result",
            input_message_content=InputTextMessageContent("No result")
        )
        await update.inline_query.answer([result], cache_time=0)
        return

    # Search the course list for matching courses
    results = []
    for course in course_list:
        course_name, course_code = course
        # Check if the query matches any part of the course name or code
        if re.search(query, course_name.lower()) or re.search(query, course_code.lower()):
            result = InlineQueryResultArticle(
                id=str(uuid4()),  # Generate unique ID for each result
                title=course_name,
                description=f"Code: {course_code}",
                input_message_content=InputTextMessageContent(f"{course_name} ({course_code})")
            )
            results.append(result)

    # If no matches found, inform the user
    if not results:
        result = InlineQueryResultArticle(
            id=str(uuid4()),
            title="Oops, your search didn't match my course list",
            description="No result",
            input_message_content=InputTextMessageContent("No result")
        )
        results.append(result)

    # Respond to the inline query with search results
    await update.inline_query.answer(results, cache_time=0)

def main():
    # Create an updater and pass your bot token
    updater = Updater("7538116284:AAE_FK1Ae2MvMgWj17z62sP6WV0Tjzy2fP8", use_context=True)

    # Register the inline query handler
    updater.dispatcher.add_handler(InlineQueryHandler(inline_query))

    # Start polling updates
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()