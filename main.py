import json
from datetime import datetime, timedelta
import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

API_TOKEN = '8152141789:AAEohBki02T1XqKxltPvhJpP72y6jz5zpMg'
DATA_FILE = 'users.json'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

def load_users():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(DATA_FILE, 'w') as f:
        json.dump(users, f, indent=2)

users = load_users()

main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add(KeyboardButton("Профиль"), KeyboardButton("Турниры"))
main_menu.add(KeyboardButton("Помощь"))

register_menu = ReplyKeyboardMarkup(resize_keyboard=True)
register_menu.add(KeyboardButton("Зарегистрироваться"))

def profile_keyboard(role="Боец"):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    if role == "Боец":
        kb.add(KeyboardButton("Пополнить баланс"))
    elif role in ["Администратор", "Разработчик"]:
        kb.add(KeyboardButton("Создать турнир"))
    kb.add(KeyboardButton("Сменить никнейм"))
    kb.add(KeyboardButton("Назад"))
    return kb

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id in users:
        await message.answer(f"Добро пожаловать обратно, @{users[user_id]['nickname']}!", reply_markup=main_menu)
    else:
        await message.answer("Привет. Чтобы продолжить, нужно зарегистрироваться.", reply_markup=register_menu)

@dp.message_handler(lambda m: m.text == "Зарегистрироваться")
async def register_handler(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id in users:
        await message.answer("Ты уже зарегистрирован.", reply_markup=main_menu)
        return
    await message.answer("Введи свой никнейм. Он будет отображаться в турнирах и в профиле.")
    dp.register_message_handler(nickname_step, content_types=['text'])

async def nickname_step(message: types.Message):
    nickname = message.text.strip()
    user_id = str(message.from_user.id)
    users[user_id] = {
        "telegram_id": user_id,
        "username": message.from_user.username,
        "nickname": nickname,
        "rank": "E",
        "mmr": 0,
        "ar_balance": 0,
        "current_tournament": None,
        "role": "Боец",
        "last_nickname_change": datetime.now().isoformat()
    }
    save_users(users)
    await message.answer(f"Готово! Ты зарегистрирован как @{nickname}", reply_markup=main_menu)
    dp.unregister_message_handler(nickname_step, content_types=['text'])

@dp.message_handler(lambda m: m.text == "Профиль")
async def profile_handler(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        await message.answer("Ты ещё не зарегистрирован. Нажми «Зарегистрироваться».", reply_markup=register_menu)
        return
    user = users[user_id]
    nickname = user['nickname']
    rank = user['rank']
    mmr = user['mmr']
    ar = user['ar_balance']
    role = user['role']
    tournament = user['current_tournament'] if user['current_tournament'] else "-"
    await message.answer(
        f"Профиль: @{nickname}\nРанг: {rank} ({mmr} MMR)\nAR: {ar}\nТурнир: {tournament}\nРоль: {role}",
        reply_markup=profile_keyboard(role)
    )

@dp.message_handler(lambda m: m.text == "Сменить никнейм")
async def change_nickname_handler(message: types.Message):
    user_id = str(message.from_user.id)
    user = users.get(user_id)
    if not user:
        await message.answer("Ты ещё не зарегистрирован.")
        return
    last_change = datetime.fromisoformat(user.get("last_nickname_change", datetime.now().isoformat()))
    if datetime.now() - last_change < timedelta(days=30):
        days_left = 30 - (datetime.now() - last_change).days
        await message.answer(f"Никнейм можно менять раз в 30 дней. Осталось: {days_left} дн.")
        return
    await message.answer("Введи новый никнейм:")
    dp.register_message_handler(nickname_update_step, content_types=['text'])

async def nickname_update_step(message: types.Message):
    user_id = str(message.from_user.id)
    new_nickname = message.text.strip()
    users[user_id]['nickname'] = new_nickname
    users[user_id]['last_nickname_change'] = datetime.now().isoformat()
    save_users(users)
    await message.answer(f"Никнейм успешно изменён на @{new_nickname}")
    dp.unregister_message_handler(nickname_update_step, content_types=['text'])

@dp.message_handler(lambda m: m.text == "Помощь")
async def help_handler(message: types.Message):
    await message.answer("Ты в системе QUAROS. Сражайся, поднимайся в ранге и зарабатывай. Скоро здесь будет больше.")

@dp.message_handler(lambda m: m.text == "Назад")
async def back_handler(message: types.Message):
    await message.answer("Главное меню:", reply_markup=main_menu)

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
