import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

# Load course data from JSON file
with open('courses_data.json') as file:
    COURSES = json.load(file)

async def handle_courses(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    # Display colleges
    keyboard = [
        [InlineKeyboardButton(college, callback_data=f"college_{college}")] for college in COURSES.keys()
    ]
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="start")])  # Back button
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Select a college 👇", reply_markup=reply_markup)

async def select_college(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    college = query.data.replace('college_', '')  # Get the college name
    context.user_data['selected_college'] = college

    if college in COURSES:
        keyboard = [
            [InlineKeyboardButton(department, callback_data=f"department_{college}_{department}")] 
            for department in COURSES[college].keys()
        ]
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="courses")])  # Back button
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"Select a department in {college} 👇", reply_markup=reply_markup)

async def select_department(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    college, department = query.data.replace('department_', '').split('_', 1)
    context.user_data['selected_college'] = college
    context.user_data['selected_department'] = department

    if college in COURSES and department in COURSES[college]:
        # Check if division exists
        if isinstance(COURSES[college][department], dict) and 'division' in COURSES[college][department]:
            keyboard = [
                [InlineKeyboardButton(division, callback_data=f"division_{college}_{department}_{division}")] 
                for division in COURSES[college][department]['division'].keys()
            ]
            keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=f"college_{college}")])  # Back button
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(f"Select a division in {department} 👇", reply_markup=reply_markup)
        else:
            await query.edit_message_text("No available divisions for this department.")
    else:
        await query.edit_message_text("Invalid selection, please try again.")

async def select_division(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    college, department, division = query.data.replace('division_', '').split('_', 2)
    context.user_data['selected_college'] = college
    context.user_data['selected_department'] = department
    context.user_data['selected_division'] = division

    if college in COURSES and department in COURSES[college] and 'division' in COURSES[college][department]:
        if isinstance(COURSES[college][department]['division'][division], dict):
            keyboard = [
                [InlineKeyboardButton(year, callback_data=f"year_{college}_{department}_{division}_{year}")] 
                for year in COURSES[college][department]['division'][division].keys()
            ]
            keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=f"department_{college}_{department}")])  # Back button
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(f"Select a year in {division} 👇", reply_markup=reply_markup)
        else:
            await query.edit_message_text("No available years for this division.")
    else:
        await query.edit_message_text("Invalid selection, please try again.")

async def select_year(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    college, department, division, year = query.data.replace('year_', '').split('_', 3)
    context.user_data['selected_college'] = college
    context.user_data['selected_department'] = department
    context.user_data['selected_division'] = division
    context.user_data['selected_year'] = year

    if college in COURSES and department in COURSES[college] and 'division' in COURSES[college][department]:
        year_data = COURSES[college][department]['division'][division].get(year)

        if isinstance(year_data, dict):
            keyboard = [
                [InlineKeyboardButton(semester, callback_data=f"semester_{college}_{department}_{division}_{year}_{semester}")] 
                for semester in year_data.keys()
            ]
            keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=f"division_{college}_{department}_{division}")])  # Back button
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(f"Select a semester for {year} in {division} 👇", reply_markup=reply_markup)
        else:
            await query.edit_message_text("No valid data for this year.")
    else:
        await query.edit_message_text("Invalid selection, please try again.")

async def select_semester(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    college, department, division, year, semester = query.data.replace('semester_', '').split('_', 4)
    context.user_data['selected_college'] = college
    context.user_data['selected_department'] = department
    context.user_data['selected_division'] = division
    context.user_data['selected_year'] = year
    context.user_data['selected_semester'] = semester

    if college in COURSES and department in COURSES[college] and 'division' in COURSES[college][department]:
        semester_data = COURSES[college][department]['division'][division][year].get(semester)

        if semester_data:
            subjects = "\n".join([f"{sub[0]} ({sub[1]})" for sub in semester_data])
            course_buttons = [
                [InlineKeyboardButton(f"📚 {sub[0]} ({sub[1]})", callback_data=f'course_{sub[1]}')] for sub in semester_data
            ]
            course_buttons.append([InlineKeyboardButton("🔙 Back", callback_data=f"year_{college}_{department}_{division}_{year}")])  # Back button
            reply_markup = InlineKeyboardMarkup(course_buttons)
            await query.edit_message_text(f"Here are the subjects for {semester}:\n\n{subjects}", reply_markup=reply_markup)
        else:
            await query.edit_message_text("No subjects available for this semester.")
    else:
        await query.edit_message_text("Invalid selection, please try again.")

async def handle_course_selection(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    c_code = query.data.replace('course_', '')
    main_btn = InlineKeyboardMarkup(row_width=1)
    main_btn.add(
        InlineKeyboardButton("📚 Books & Reference", callback_data=f'material_{c_code}'),
        InlineKeyboardButton("🗞 Course Outline", callback_data=f'outline_{c_code}'),
        InlineKeyboardButton("📝 Last Year Exams", callback_data=f'exams_{c_code}'),
        InlineKeyboardButton("🔙 Back", callback_data=f'semester_{context.user_data["selected_college"]}_{context.user_data["selected_department"]}_{context.user_data["selected_division"]}_{context.user_data["selected_year"]}')  # Back button
    )

    await query.edit_message_text(f"Select an option for the course {c_code}:", reply_markup=main_btn)


