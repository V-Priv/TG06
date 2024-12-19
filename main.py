import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import sqlite3
import logging
import requests
import random
from config import TOKEN

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Создание бота и диспетчера
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Создание клавиатуры
button_registr = KeyboardButton(text="Регистрация в телеграм-боте")
button_exchange_rates = KeyboardButton(text="Курс валют")
button_tips = KeyboardButton(text="Советы по экономии")
button_finances = KeyboardButton(text="Личные финансы")
keyboard = ReplyKeyboardMarkup(keyboard=[
    [button_registr, button_exchange_rates],
    [button_tips, button_finances]
], resize_keyboard=True)

# Настройка базы данных
conn = sqlite3.connect('user.db')
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    telegram_id INTEGER UNIQUE,
    name TEXT,
    category1 TEXT,
    category2 TEXT,
    category3 TEXT,
    expenses1 REAL,
    expenses2 REAL,
    expenses3 REAL
)
''')
conn.commit()

# Определение состояний
class FinancesForm(StatesGroup):
    category1 = State()
    expenses1 = State()
    category2 = State()
    expenses2 = State()
    category3 = State()
    expenses3 = State()

# Обработчик команды /start
@dp.message(CommandStart())
async def send_start(message: Message, bot: Bot):
    await bot.send_message(message.chat.id, "Привет! Я ваш личный финансовый помощник. "
                                            "Выберите одну из опций в меню:", reply_markup=keyboard)

# Обработчик регистрации
@dp.message(F.text == "Регистрация в телеграм-боте")
async def registration(message: Message, bot: Bot):
    telegram_id = message.from_user.id
    name = message.from_user.full_name
    cursor.execute('''SELECT * FROM users WHERE telegram_id = ?''', (telegram_id,))
    user = cursor.fetchone()
    if user:
        await bot.send_message(message.chat.id, "Вы уже зарегистрированы!")
    else:
        cursor.execute('''INSERT INTO users (telegram_id, name) VALUES (?, ?)''', (telegram_id, name))
        conn.commit()
        await bot.send_message(message.chat.id, "Вы успешно зарегистрированы!")

# Обработчик курса валют
@dp.message(F.text == "Курс валют")
async def exchange_rates(message: Message, bot: Bot):
    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    try:
        response = requests.get(url)
        if response.status_code != 200:
            await bot.send_message(message.chat.id, "Не удалось получить данные о курсе валют!")
            return
        data = response.json()
        usd_to_rub = data['Valute']['USD']['Value']
        eur_to_rub = data['Valute']['EUR']['Value']
        await bot.send_message(message.chat.id, f"1 USD = {usd_to_rub:.2f} RUB\n"
                                                f"1 EUR = {eur_to_rub:.2f} RUB")
    except Exception as e:
        await bot.send_message(message.chat.id, "Произошла ошибка при получении данных о курсе валют.")
        logging.error(e)

# Обработчик советов по экономии
@dp.message(F.text == "Советы по экономии")
async def send_tips(message: Message, bot: Bot):
    tips = [
        "Совет 1: Ведите бюджет и следите за своими расходами.",
        "Совет 2: Откладывайте часть доходов на сбережения.",
        "Совет 3: Покупайте товары по скидкам и распродажам."
    ]
    tip = random.choice(tips)
    await bot.send_message(message.chat.id, tip)

# Обработчик личных финансов
@dp.message(F.text == "Личные финансы")
async def finances(message: Message, state: FSMContext):
   await state.set_state(FinancesForm.category1)
   await message.reply("Введите первую категорию расходов:")

# Обработчик первой категории расходов
@dp.message(FinancesForm.category1)
async def finances(message: Message, state: FSMContext):
   await state.update_data(category1 = message.text)
   await state.set_state(FinancesForm.expenses1)
   await message.reply("Введите расходы для категории 1:")

# Обработчик расходов для первой категории
@dp.message(FinancesForm.expenses1)
async def finances(message: Message, state: FSMContext):
   await state.update_data(expenses1 = float(message.text))
   await state.set_state(FinancesForm.category2)
   await message.reply("Введите вторую категорию расходов:")

@dp.message(FinancesForm.category2)
async def finances(message: Message, state: FSMContext):
   await state.update_data(category2 = message.text)
   await state.set_state(FinancesForm.expenses2)
   await message.reply("Введите расходы для категории 2:")

@dp.message(FinancesForm.expenses2)
async def finances(message: Message, state: FSMContext):
   await state.update_data(expenses2 = float(message.text))
   await state.set_state(FinancesForm.category3)
   await message.reply("Введите третью категорию расходов:")

@dp.message(FinancesForm.category3)
async def finances(message: Message, state: FSMContext):
   await state.update_data(category3 = message.text)
   await state.set_state(FinancesForm.expenses3)
   await message.reply("Введите расходы для категории 3:")

@dp.message(FinancesForm.expenses3)
async def finances(message: Message, state: FSMContext):
   data = await state.get_data()
   telegram_id = message.from_user.id
   cursor.execute('''UPDATE users SET category1 = ?, expenses1 = ?, category2 = ?, expenses2 = ?, category3 = ?, expenses3 = ? WHERE telegram_id = ?''',
                  (data['category1'], data['expenses1'], data['category2'], data['expenses2'], data['category3'], float(message.text), telegram_id))
   conn.commit()
   await state.clear()

   await message.answer("Категории и расходы сохранены!")





if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
