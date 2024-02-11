from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from workers.database import init_user, create_connection
from keyboards.menu_keyboards import start_keyboard


router = Router()

user_collection = create_connection()


@router.message(Command('start'))
async def start_handler(message: Message):
    user_id = message.from_user.id
    init_user(user_collection, user_id)
    start_message = (
        'Welcome to the game Gucotomap! 🗺\n'
        'In this game you have to guess countries by satellite images of their cities🧐\n'
        'To start playing click on the Play button 🎮\n'
    )
    await message.answer(start_message, reply_markup=start_keyboard)


@router.message(Command('help'))
async def help_handler(message: Message):
    help_message = (
        'To start playing you need to tap "Play"\n\n'
        'The rules of this game📃\n'
        '- A satellite image of the city appears in front of you🏙\n'
        '- There are  4️⃣ options for which country the city belongs to\n'
        '- Click on the suggested answer❓\n'
        '- If the answer is correct✅, you get 1 point for the correct answer\n'
        '- If the answer is wrong❌, you are taken off one attempt and the correct answer is shown.\n'
        '-The total number of incorrect attempts per game is 5️⃣.\n\n'
        'Have a good game🤗'
    )
    await message.answer(help_message)


@router.message(Command('admin'))
async def no_admin_show_manual(message: Message):
    manual_no_admin_message = (
        'You do not have access to admin commands'
    )
    await message.answer(manual_no_admin_message)


@router.message(F.text == 'Get user id')
async def admin_get_user_id(message: Message):
    user_id_info = f"Your user id: <code>{message.from_user.id}</code>"
    await message.answer(user_id_info)
