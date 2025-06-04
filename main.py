
import json
import asyncio
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart, Text

# === Настройки ===
TOKEN = '8152141789:AAEohBki02T1XqKxltPvhJpP72y6jz5zpMg'
DATA_FILE = 'users.json'

bot = Bot(token=TOKEN)
dp = Dispatcher()

# === Загрузка и сохранение базы ===
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

# === Кнопки ===
main_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='🧍 Профиль'), KeyboardButton(text='🏆 Турниры')],
    [KeyboardButton(text='❓ Помощь')],
], resize_keyboard=True)

register_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='🔐 Зарегистрироваться')]
], resize_keyboard=True)

# === Команда /start ===
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = str(message.from_user.id)

    if user_id in users:
        await message.answer(f"Добро пожаловать обратно, @{users[user_id]['nickname']}!", reply_markup=main_menu)
    else:
        await message.answer("Привет. Чтобы продолжить, нужно зарегистрироваться.", reply_markup=register_menu)

# === Регистрация ===
@dp.message(Text("🔐 Зарегистрироваться"))
async def register_handler(message: types.Message):
    user_id = str(message.from_user.id)

    if user_id in users:
        await message.answer("Ты уже зарегистрирован.", reply_markup=main_menu)
        return

    await message.answer("Введи свой никнейм. Он будет отображаться в турнирах и в профиле.")
    dp.message.register(nickname_step)

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

# === Профиль ===
@dp.message(Text("🧍 Профиль"))
async def profile_handler(message: types.Message):
    user_id = str(message.from_user.id)

    if user_id not in users:
        await message.answer("Ты ещё не зарегистрирован. Нажми «🔐 Зарегистрироваться».", reply_markup=register_menu)
        return

    user = users[user_id]
    nickname = user['nickname']
    rank = user['rank']
    mmr = user['mmr']
    ar = user['ar_balance']
    role = user['role']
    tournament = user['current_tournament'] if user['current_tournament'] else "—"

    buttons = []
    if role == "Боец":
        buttons.append([KeyboardButton(text="💳 Пополнить баланс")])
    elif role in ["Администратор", "Разработчик"]:
        buttons.append([KeyboardButton(text="⚔️ Создать турнир")])

    buttons.append([KeyboardButton(text="✏️ Сменить никнейм")])
    buttons.append([KeyboardButton(text="⬅️ Назад")])
    reply = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

    await message.answer(
        f"🧍‍♂️ Профиль: @{nickname}
📈 Ранг: {rank} ({mmr} MMR)
💠 AR: {ar}
🎯 Турнир: {tournament}
🎖 Роль: {role}",
        reply_markup=reply
    )

# === Смена никнейма ===
@dp.message(Text("✏️ Сменить никнейм"))
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
    dp.message.register(nickname_update_step)

async def nickname_update_step(message: types.Message):
    user_id = str(message.from_user.id)
    new_nickname = message.text.strip()

    users[user_id]['nickname'] = new_nickname
    users[user_id]['last_nickname_change'] = datetime.now().isoformat()
    save_users(users)

    await message.answer(f"Никнейм успешно изменён на @{new_nickname}")

# === Помощь ===
@dp.message(Text("❓ Помощь"))
async def help_handler(message: types.Message):
    await message.answer("Ты в системе QUAROS. Сражайся, поднимайся в ранге и зарабатывай.
Скоро здесь будет больше.")

# === Назад ===
@dp.message(Text("⬅️ Назад"))
async def back_handler(message: types.Message):
    await message.answer("Главное меню:", reply_markup=main_menu)

# === Запуск ===
async def main():
    print("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
