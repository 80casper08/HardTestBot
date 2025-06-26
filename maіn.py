import asyncio import os from aiogram import Bot, Dispatcher, types, F from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery from aiogram.fsm.storage.memory import MemoryStorage from flask import Flask from threading import Thread from questions import sections from dotenv import load_dotenv

load_dotenv() TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN) dp = Dispatcher(storage=MemoryStorage())

user_data = {}

Flask вебсервер для підтримки 24/7

app = Flask(name)

@app.route('/') def home(): return "🟢 Бот працює!"

def run_flask(): app.run(host='0.0.0.0', port=8080)

def keep_alive(): Thread(target=run_flask).start()

Кнопки розділів

def get_sections_keyboard(): kb = InlineKeyboardMarkup() for key in sections: kb.add(InlineKeyboardButton(text=key, callback_data=key)) return kb

@dp.message(F.text == "/start") async def cmd_start(message: types.Message): await message.answer("Оберіть розділ:", reply_markup=get_sections_keyboard())

@dp.callback_query(F.data.in_(sections.keys())) async def start_quiz(callback: CallbackQuery): category = callback.data user_id = callback.from_user.id question_set = sections[category] for q in question_set: random.shuffle(q['options']) user_data[user_id] = { "questions": question_set, "q_index": 0, "score": 0, "selected": set() } await send_question(callback)

@dp.callback_query(F.data.startswith("opt_")) async def handle_option(callback: CallbackQuery): user_id = callback.from_user.id data =

