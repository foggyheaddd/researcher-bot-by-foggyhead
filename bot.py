# bot.py
import os
import random
import json
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import logging

# === Google Sheets (современный способ) ===
import gspread
from google.oauth2.service_account import Credentials

# === Конфигурация ===
BOT_TOKEN = os.getenv("BOT_TOKEN", "8495367324:AAHNP5u3wrRRCxUBOa6VAi3xNZi_ctKaO0U")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "892637733")
GOOGLE_SHEET_KEY = os.getenv("GOOGLE_SHEET_KEY", "1rW615gmemSRK-vaQx5C6sGbv1feLH8V_LaLYAd_7rP0")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")

# Авторизация в Google
if GOOGLE_CREDENTIALS_JSON:
    creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
    creds = Credentials.from_service_account_info(creds_dict, scopes=[
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ])
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(GOOGLE_SHEET_KEY).sheet1
else:
    sheet = None
    logging.warning("Google Sheets не настроен")

# === Бот ===
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# === PANAS ===
PANAS_ITEMS = [
    ("Внимательный", "pos"),
    ("Радостный", "pos"),
    ("Уверенный", "pos"),
    ("Сосредоточенный", "pos"),
    ("Увлечённый", "pos"),
    ("Решительный", "pos"),
    ("Вдохновленный", "pos"),
    ("Полный сил", "pos"),
    ("Заинтересованный", "pos"),
    ("Бодрый", "pos"),
    ("Подавленный", "neg"),
    ("Расстроенный", "neg"),
    ("Виноватый", "neg"),
    ("Злой", "neg"),
    ("Раздраженный", "neg"),
    ("Стыдящийся", "neg"),
    ("Нервный", "neg"),
    ("Беспокойный", "neg"),
    ("Тревожный", "neg"),
    ("Испуганныный", "neg")
]
random.shuffle(PANAS_ITEMS)

# === Утверждения ===
STATEMENTS = [
    {"id": f"ps_{i+1}", "text": text, "type": "pseudoscience"}
    for i, text in enumerate([
        "Люди, которые заваривают кофе, стоя лицом к окну, реже теряют важные вещи в течение дня.","Сон в пижаме, вывернутой наизнанку, улучшает способность замечать скрытые совпадения на следующий день.",
        "Те, кто используют только левый карман для мелочи, принимают более «лёгкие» решения в стрессовых ситуациях.",
        "Чтение книг задом наперёд (от последней страницы к первой) усиливает интуицию в личных отношениях.",
        "Люди, которые моют посуду в порядке убывания размера тарелок, лучше предвидят последствия своих слов.",
        "Ношение носков разного цвета по чётным и нечётным дням улучшает баланс между работой и личной жизнью.",
        "Те, кто солят еду до того, как увидят блюдо, чаще чувствуют внутреннюю ясность по утрам.",
        "Люди, которые ходят по лестнице, начиная с левой ноги, быстрее восстанавливаются после эмоциональных разговоров.",
        "Просмотр погоды на неделю вперёд по утрам повышает способность замечать возможности, которые упускают другие.",
        "Те, кто складывают купюры «лицом вниз» в кошельке, реже сомневаются в своих крупных решениях.",
        "Люди, которые чихают при дневном свете, обладают более точной интуицией в финансовых вопросах.",
        "Регулярное использование ручки, подаренной кем-то дорогим, улучшает память на обещания, данные другим.",
        "Те, кто едят первый кусок завтрака, сидя на самом краю стула, легче находят выход из тупиковых ситуаций.",
        "Люди, которые выключают свет локтем (а не рукой), лучше чувствуют скрытые эмоции в голосе собеседника.",
        "Хранение чеков от покупок в отдельном конверте с надписью «было» усиливает чувство контроля над будущим.",
        "Те, кто смотрят на своё отражение в зеркале, произнося имя вслух, реже принимают решения из чувства вины.",
        "Люди, которые кладут телефон экраном вверх только по вторникам, чаще замечают «знаки» в повседневной жизни.",
        "Ношение ремня на одну дырочку туже обычного повышает устойчивость к чужому негативу в течение дня.",
        "Те, кто пьют воду, сделав три глотка подряд, а потом паузу, лучше понимают, чего хотят на самом деле.",
        "Люди, которые закрывают глаза на три секунды перед входом в новое помещение, чаще выбирают «правильное» время для слов."
        # ... остальные 19 псевдонаучных
    ])
] + [
    {"id": f"sc_{i+1}", "text": text, "type": "science"}
    for i, text in enumerate([
        "В регионах с частыми, но слабыми землетрясениями разрушения от сильных толчков обычно меньше.","Ночное освещение улиц в городах снижает популяции насекомых-опылителей в пригородных зонах.",
        "Дети, растущие в двуязычной среде, быстрее переключаются между задачами, требующими разного типа внимания.",
        "Люди чаще выбирают «бесплатный» вариант, даже если он объективно хуже платного.",
        "Анализ пыльцы в слоях почвы позволяет точно реконструировать сельское хозяйство древних цивилизаций.",
        "Повышение средней температуры на 1°C увеличивает частоту экстремальных ливней в умеренных широтах.",
        "Люди хуже запоминают информацию, если знают, что она сохранена в цифровом виде.",
        "Выращивание растений в смешанных посевах снижает распространение грибковых заболеваний по сравнению с монокультурами.",
        "Объяснение ошибок при решении задач улучшает понимание математики сильнее, чем повторение правильных решений.",
        "Солнечные панели в пустынных регионах вырабатывают больше энергии зимой, чем летом, из-за перегрева.",
        "Наличие зелёных насаждений вдоль дорог снижает уровень шума в жилых домах на 3–5 децибел.",
        "В культурах с сильной ориентацией на будущее выше уровень сбережений домохозяйств.",
        "Учёные из стран с высоким уровнем гендерного равенства чаще публикуют совместные работы.",
        "Человеческий глаз способен различать изменения яркости при разнице всего в 1–2%.",
        "После 40 лет регулярное кардиоупражнение замедляет уменьшение объёма гиппокампа.",
        "Введение платы за пластиковые пакеты снижает их использование быстрее, чем информационные кампании.",
        "Обратная связь, данная через день после теста, усваивается лучше, чем сразу после.",
        "Люди лучше запоминают информацию, если объясняют её кому-то вслух, а не просто перечитывают.",
        "Умственная работоспособность у большинства людей снижается в помещениях с температурой выше 26°C.",
        "В городах с развитой велосипедной инфраструктурой выше общий уровень физической активности населения."
        # ... остальные 19 научных
    ])
]
random.shuffle(STATEMENTS)

# === FSM ===
class Survey(StatesGroup):
    consent = State()
    health = State()
    gender = State()
    age = State()
    field = State()
    panas_instruction = State()
    panas1 = State()
    video_watched = State()
    panas2_instruction = State()
    panas2 = State()
    statements = State()
    feedback = State()

# === Клавиатуры ===
def rating_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=str(i)) for i in range(1, 6)]],
        resize_keyboard=True, one_time_keyboard=True
    )

def gender_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton("Мужской"), KeyboardButton("Женский")]],
        resize_keyboard=True, one_time_keyboard=True
    )

def yes_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton("Да, согласен(а)")]],
        resize_keyboard=True, one_time_keyboard=True
    )

def health_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton("Да, подтверждаю")]],
        resize_keyboard=True, one_time_keyboard=True
    )

def understood_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton("Понял")]],
        resize_keyboard=True, one_time_keyboard=True
    )

def video_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton("Всё, посмотрел")]],
        resize_keyboard=True, one_time_keyboard=True
    )

# === Вспомогательные функции ===
async def safe_delete(chat_id: int, msg_id: int):
    try:
        await bot.delete_message(chat_id, msg_id)
    except:
        pass

# === Хендлеры ===
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("⚠️ Добро пожаловать!", reply_markup=yes_kb())
    await state.set_state(Survey.consent)

@dp.message(Survey.consent, F.text.lower() == "да, согласен(а)")
async def process_consent(message: Message, state: FSMContext):
    await message.answer("Подтверждаете здоровье?", reply_markup=health_kb())
    await state.set_state(Survey.health)

@dp.message(Survey.health, F.text.lower() == "да, подтверждаю")
async def process_health(message: Message, state: FSMContext):
    await message.answer("Пол:", reply_markup=gender_kb())
    await state.set_state(Survey.gender)

# ... (остальные хендлеры аналогично)

@dp.message(Survey.video_watched, F.text.lower() == "всё, посмотрел")
async def video_watched(message: Message, state: FSMContext):
    # Удаляем сообщение пользователя
    await safe_delete(message.chat.id, message.message_id)
    # Удаляем видео
    data = await state.get_data()
    if 'video_msg_id' in data:
        await safe_delete(message.chat.id, data['video_msg_id'])
    # Переходим к PANAS-2
    await message.answer("Теперь оцените состояние...", reply_markup=understood_kb())
    await state.set_state(Survey.panas2_instruction)

# === Отправка видео с сохранением ID ===
async def send_video_with_remember(chat_id: int, video_id: str, state: FSMContext):
    msg = await bot.send_video(chat_id, video_id)
    await state.update_data(video_msg_id=msg.message_id)

# === Сохранение в Google Sheets ===
async def save_to_sheet(data: dict):
    if not sheet:
        return
    # Формируем строку (10 + 160 = 170 колонок)
    row = [
        data.get('user_id', ''),
        data.get('tg_username', 'нет'),
        data.get('gender', ''),
        data.get('age', ''),
        data.get('field', ''),
        data.get('group', ''),
        data.get('panas1_pos', ''),
        data.get('panas1_neg', ''),
        data.get('panas2_pos', ''),
        data.get('panas2_neg', ''),
    ]
    # ... добавляем 40 утверждений × 4
    sheet.append_row(row)

# === Webhook ===
@dp.startup()
async def on_startup(dispatcher: Dispatcher):
    await bot.set_webhook(f"{os.getenv('RENDER_EXTERNAL_URL', '')}/webhook")

def main():
    app = web.Application()
    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    app.router.add_post("/webhook", webhook_handler.handle)
    setup_application(app, dp, bot=bot)
    web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    dp.startup.register(lambda: on_startup(bot, os.getenv("RENDER_EXTERNAL_URL", "")))
