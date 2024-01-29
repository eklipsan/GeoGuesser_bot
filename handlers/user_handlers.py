from aiogram import Router, types, F
from workers.map_worker import receive_quiz_setup, ChosenTown
from keyboards.user_keyboards import create_keyboard_countries, lost_game_keyboard
from keyboards.service_keyboards import start_keyboard
from access_filters.tg_filter import IsAdmin
from workers.database import create_connection
from workers.database import (
    init_user,
    check_user_game_status,
    start_user_game,
    check_positive_attempts,
    increase_user_score,
    get_user_info,
    decrease_user_attempts,
    finish_user_game
)


router: Router = Router()


# Set up variables to keep track of the user's game state,
# including the number of attempts.
ATTEMPTS = 5

# Create mongodb connection for user data storage
user_collection = create_connection()

# Declare variables, that used in other modules
countries = set()
town = ChosenTown(town_name=None, town_values=None)


async def setup_quiz(message: types.Message):
    """
    Sets up a quiz by retrieving a random town and associated map data.
    Creates a keyboard for selecting countries and sends a photo to the user.
    """
    global town, countries
    town, map, countries = receive_quiz_setup()
    keyboard = create_keyboard_countries(countries=countries)

    print(town.town_name)
    print(town.town_values)
    await message.answer_photo(
        map.url_link,
        reply_markup=keyboard,
        caption='What country is this?'
    )


@router.message(F.text == "Play")
async def start_quiz(message: types.Message):
    "Message handler that starts the quiz game."
    global user_collection, ATTEMPTS
    user_id = message.from_user.id
    init_user(user_collection, user_id, ATTEMPTS)
    if check_user_game_status(user_collection, user_id):
        await message.answer("You are already in the game")
    else:
        start_user_game(user_collection, user_id)
        await setup_quiz(message)


async def next_quiz(message: types.Message):
    "This function sets up the next quiz."
    await setup_quiz(message)


@router.message(lambda message: message.text in countries)
async def check_answer(message: types.Message):
    """
    Message handler that checks the user's answer during the quiz game.
    It updates the user's score and attempts.
    Proceeds to the next quiz or ends the game based on the user's answer.
    """
    global user_collection, ATTEMPTS
    user_id = message.from_user.id
    if check_user_game_status(user_collection, user_id):
        if message.text == town.town_values['country']:
            increase_user_score(user_collection, user_id)
            user_score, _ = get_user_info(user_collection, user_id)
            good_job_message = f"🌟 GOOD JOB!🌟\nYour current score is {user_score}.\nKeep it going!✨"
            await message.answer(good_job_message)
            await next_quiz(message)
        elif message.text != town.town_values['country'] and check_positive_attempts(user_collection, user_id):
            decrease_user_attempts(user_collection, user_id)
            _, user_attempts = get_user_info(user_collection, user_id)
            await message.answer(f"Oops!😬\nThe right answer is {town.town_values['country']}.\nYou have {user_attempts} attempts left.")
            await next_quiz(message)
        else:
            finish_user_game(user_collection, user_id, ATTEMPTS)
            user_score, _ = get_user_info(user_collection, user_id)
            await message.answer(
                f"Sorry, but you've used up all your {ATTEMPTS} attempts😿. Your score is {user_score}.",
                reply_markup=lost_game_keyboard
            )
    else:
        await message.answer(
            "If you want to play again, choose the 'Play' button.🎮",
            reply_markup=lost_game_keyboard
        )


@router.message(F.text == 'Cancel the game')
async def cancel_game(message: types.Message):
    "Message handler that cancels the game and returns the user to the main menu."
    user_id = message.from_user.id
    finish_user_game(user_collection, user_id, ATTEMPTS)
    await message.answer(
        "You have canceled the game. You are in the main menu",
        reply_markup=start_keyboard
    )


@router.message(F.text == "Go to main menu")
async def get_main_menu(message: types.Message):
    "Message handler that displays a message indicating that the user is in the main menu."
    await message.answer(
        "You are in the main menu",
        reply_markup=start_keyboard
    )


@router.message(IsAdmin() and F.text == 'Get answer')
async def admin_get_answer(message: types.Message):
    '''
    Handler, that returns the right current answer.
    It works only for admins.
    '''
    admin_answer_text = f"Town: {town.town_name}\nTown values: {town.town_values}"
    await message.answer(admin_answer_text)
