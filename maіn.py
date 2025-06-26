
import asyncio
import os
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from flask import Flask
from threading import Thread
from dotenv import load_dotenv
from questions import op_questions, general_questions, lean_questions, hard_questions

load_dotenv()
TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class QuizState(StatesGroup):
    category = State()
    question_index = State()
    selected_options = State()
    score = State()
    total = State()

user_data = {}

def get_keyboard(options, selected_indices):
    buttons = []
    for i, (text, _) in enumerate(options):
        prefix = "✅ " if i in selected_indices else ""
        buttons.append([InlineKeyboardButton(text=prefix + text, callback_data=f"option_{i}")])
    buttons.append([InlineKeyboardButton(text="✅ Підтвердити", callback_data="confirm")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(F.text == "/start")
async def start_handler(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🎁 ОП", callback_data="op")],
        [InlineKeyboardButton("📚 Загальні", callback_data="general")],
        [InlineKeyboardButton("⚙️ Lean", callback_data="lean")],
        [InlineKeyboardButton("💪 Hard Test", callback_data="hard")],
    ])
    await message.answer("Вибери розділ тесту:", reply_markup=keyboard)
    await state.clear()

@dp.callback_query(F.data.in_(["op", "general", "lean", "hard"]))
async def select_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data
    questions = {
        "op": op_questions,
        "general": general_questions,
        "lean": lean_questions,
        "hard": hard_questions,
    }[category]
    random.shuffle(questions)
    await state.update_data(
        category=category,
        question_index=0,
        selected_options=[],
        score=0,
        total=len(questions),
        questions=questions,
    )
    await send_question(callback.message, state)

async def send_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    index = data["question_index"]
    questions = data["questions"]
    if index >= len(questions):
        await finish_quiz(message, state)
        return
    question = questions[index]
    selected = data.get("selected_options", [])
    keyboard = get_keyboard(question["options"], selected)
    await message.answer(question['text'], reply_markup=keyboard)

@dp.callback_query(F.data.startswith("option_"))
async def toggle_option(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    index = int(callback.data.split("_")[1])
    selected = data.get("selected_options", [])
    if index in selected:
        selected.remove(index)
    else:
        selected.append(index)
    await state.update_data(selected_options=selected)
    await callback.message.edit_reply_markup(reply_markup=get_keyboard(
        data["questions"][data["question_index"]]["options"],
        selected
    ))
    await callback.answer()

@dp.callback_query(F.data == "confirm")
async def confirm_answer(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    question = data["questions"][data["question_index"]]
    correct_indices = [i for i, opt in enumerate(question["options"]) if opt[1]]
    selected = data["selected_options"]
    if set(correct_indices) == set(selected):
        data["score"] += 1
    data["question_index"] += 1
    data["selected_options"] = []
    await state.set_data(data)
    await send_question(callback.message, state)

async def finish_quiz(message: types.Message, state: FSMContext):
    data = await state.get_data()
    score = data["score"]
    total = data["total"]
    percent = round(score / total * 100)
    if percent >= 90:
        result = "💯 Відмінно"
    elif percent >= 70:
        result = "👍 Добре"
    elif percent >= 50:
        result = "👌 Задовільно"
    else:
        result = "❌ Погано"
    await message.answer(f"Тест завершено!
Результат: {score}/{total} ({percent}%)
Оцінка: {result}")
    await state.clear()

# Flask
app = Flask(__name__)
@app.route('/')
def home():
    return "🟢 Бот працює!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run_flask).start()

async def main():
    keep_alive()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
