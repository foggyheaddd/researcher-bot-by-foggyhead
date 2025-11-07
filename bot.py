import os
import random
import json
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.filters import Command
from oauth2client.service_account import ServiceAccountCredentials
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import logging
from config import BOT_TOKEN

# === Загрузка переменных окружения (без .env) ===
# Убедись, что переменные заданы в PyCharm → Edit Configurations → Environment variables

# === Google Sheets ===
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", SCOPE)
CLIENT = gspread.authorize(CREDS)
SHEET = CLIENT.open_by_key(GOOGLE_SHEET_KEY).sheet1

# === Бот ===
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# === PANAS: 20 эмоций из твоей таблицы ===
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
    ("Испуганный", "neg")
]
random.shuffle(PANAS_ITEMS)

# === Утверждения ===
STATEMENTS = [
                 {"id": f"ps_{i + 1}", "text": text, "type": "pseudoscience"}
                 for i, text in enumerate([
        "Люди, которые заваривают кофе, стоя лицом к окну, реже теряют важные вещи в течение дня.",
        "Сон в пижаме, вывернутой наизнанку, улучшает способность замечать скрытые совпадения на следующий день.",
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
    ])
             ] + [
                 {"id": f"sc_{i + 1}", "text": text, "type": "science"}
                 for i, text in enumerate([
        "В регионах с частыми, но слабыми землетрясениями разрушения от сильных толчков обычно меньше.",
        "Ночное освещение улиц в городах снижает популяции насекомых-опылителей в пригородных зонах.",
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
    ])
             ]
random.shuffle(STATEMENTS)

# === Пример стикера (опционально) ===
STICKER_ID = "CAACAgIAAxkBAAE9dzRpDFeSN0fLldATR5H9HD8QE67hggACPhsAAktjIEvyPAAB1ZmINQE2BA"  # ← file_id стикера

# === FSM States ===
class Survey(StatesGroup):
    consent = State()
    health = State()
    gender = State()
    age = State()
    field = State()
    panas_instruction = State()
    panas1 = State()
    video_watched = State()  # ← новое состояние
    panas2_instruction = State()
    panas2 = State()
    statements = State()
    feedback = State()  # ← новое состояние


# === Клавиатуры ===
def rating_keyboard():
    return types.ReplyKeyboardMarkup([[str(i) for i in range(1, 6)]], one_time_keyboard=True, resize_keyboard=True)


def gender_keyboard():
    return types.ReplyKeyboardMarkup([["Мужской", "Женский"]], one_time_keyboard=True, resize_keyboard=True)


def yes_keyboard():
    return types.ReplyKeyboardMarkup([["Да, согласен(а)"]], one_time_keyboard=True, resize_keyboard=True)


def health_keyboard():
    return types.ReplyKeyboardMarkup([["Да, подтверждаю"]], one_time_keyboard=True, resize_keyboard=True)


def understood_keyboard():
    return types.ReplyKeyboardMarkup([["Понял"]], one_time_keyboard=True, resize_keyboard=True)


def video_watched_keyboard():
    return types.ReplyKeyboardMarkup([["Всё, посмотрел"]], one_time_keyboard=True, resize_keyboard=True)


# === Удаление сообщений ===
async def safe_delete_message(chat_id: int, message_id: int):
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass


async def send_and_track(message: types.Message, text: str, reply_markup=None):
    sent = await message.answer(text, reply_markup=reply_markup)
    return sent.message_id


# === /start ===
@dp.message_handler(commands=['start'], state='*')
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    await bot.send_sticker(message.chat.id, STICKER_ID)
    username = message.from_user.username or "нет"
    await state.update_data(tg_username=username, user_id=message.from_user.id)

    consent_text = (
        "⚠️ Перед началом участия в исследовании просим ознакомиться с условиями:\n\n"
        "1. Вы даёте согласие на обработку следующих данных: пол, возраст, сфера деятельности, ответы на психологические тесты.\n"
        "2. Данные используются исключительно в научных целях, анонимизируются и не передаются третьим лицам.\n"
        "3. Участие добровольное. Вы можете прервать его в любой момент.\n\n"
        "✅ Нажмите «Да, согласен(а)», если вы согласны."
    )
    data = await state.get_data()
    if 'last_bot_msg_id' in data:
        await safe_delete_message(message.chat.id, data['last_bot_msg_id'])
    await safe_delete_message(message.chat.id, message.message_id)
    new_msg_id = await send_and_track(message, consent_text, yes_keyboard())
    await state.update_data(last_bot_msg_id=new_msg_id)
    await Survey.consent.set()


@dp.message_handler(state=Survey.consent)
async def process_consent(message: types.Message, state: FSMContext):
    await safe_delete_message(message.chat.id, message.message_id)
    data = await state.get_data()
    if 'last_bot_msg_id' in data:
        await safe_delete_message(message.chat.id, data['last_bot_msg_id'])
    if "да" not in message.text.lower():
        await message.answer("К сожалению, без согласия участие невозможно. Спасибо за внимание!")
        return
    await state.update_data(consent=True)
    health_text = (
        "⚠️ Важно: исследование не рекомендуется лицам с психиатрическими или неврологическими заболеваниями.\n\n"
        "Подтверждаете ли вы, что у вас отсутствуют такие диагнозы?\n"
        "✅ Нажмите «Да, подтверждаю», если подтверждаете."
    )
    new_msg_id = await send_and_track(message, health_text, health_keyboard())
    await state.update_data(last_bot_msg_id=new_msg_id)
    await Survey.health.set()


@dp.message_handler(state=Survey.health)
async def process_health(message: types.Message, state: FSMContext):
    await safe_delete_message(message.chat.id, message.message_id)
    data = await state.get_data()
    if 'last_bot_msg_id' in data:
        await safe_delete_message(message.chat.id, data['last_bot_msg_id'])
    if "да" not in message.text.lower():
        await message.answer("Спасибо за честность! Участие в исследовании не рекомендуется. Берегите себя!")
        return
    await state.update_data(health=True)
    new_msg_id = await send_and_track(message, "Выберите ваш пол:", gender_keyboard())
    await state.update_data(last_bot_msg_id=new_msg_id)
    await Survey.gender.set()


@dp.message_handler(state=Survey.gender)
async def process_gender(message: types.Message, state: FSMContext):
    await safe_delete_message(message.chat.id, message.message_id)
    data = await state.get_data()
    if 'last_bot_msg_id' in data:
        await safe_delete_message(message.chat.id, data['last_bot_msg_id'])
    if message.text not in ["Мужской", "Женский"]:
        new_msg_id = await send_and_track(message, "Пожалуйста, используйте кнопки:", gender_keyboard())
        await state.update_data(last_bot_msg_id=new_msg_id)
        return
    await state.update_data(gender=message.text)
    new_msg_id = await send_and_track(message, "Укажите ваш возраст (целое число):")
    await state.update_data(last_bot_msg_id=new_msg_id)
    await Survey.age.set()


@dp.message_handler(state=Survey.age)
async def process_age(message: types.Message, state: FSMContext):
    await safe_delete_message(message.chat.id, message.message_id)
    data = await state.get_data()
    if 'last_bot_msg_id' in data:
        await safe_delete_message(message.chat.id, data['last_bot_msg_id'])
    if not message.text.isdigit():
        new_msg_id = await send_and_track(message, "Введите возраст цифрами:")
        await state.update_data(last_bot_msg_id=new_msg_id)
        return
    await state.update_data(age=int(message.text))
    new_msg_id = await send_and_track(message, "Сфера деятельности или увлечения:")
    await state.update_data(last_bot_msg_id=new_msg_id)
    await Survey.field.set()


@dp.message_handler(state=Survey.field)
async def process_field(message: types.Message, state: FSMContext):
    await safe_delete_message(message.chat.id, message.message_id)
    data = await state.get_data()
    if 'last_bot_msg_id' in data:
        await safe_delete_message(message.chat.id, data['last_bot_msg_id'])
    await state.update_data(field=message.text.strip())
    group = random.choice([1, 2, 3])
    await state.update_data(group=group)

    instruction_text = (
        "Сейчас вы пройдёте тест на эмоциональное состояние.\n\n"
        "Определите своё состояние с помощью прилагательных, оценивая то, насколько хорошо оно вас описывает сейчас, "
        "по 5-балльной шкале:\n"
        "1 — совсем не согласен(а)\n"
        "5 — полностью согласен(а)"
    )
    new_msg_id = await send_and_track(message, instruction_text, understood_keyboard())
    await state.update_data(last_bot_msg_id=new_msg_id)
    await Survey.panas_instruction.set()


# === Хендлеры кнопки "Понял" ===
@dp.message_handler(lambda m: m.text == "Понял", state=Survey.panas_instruction)
async def panas_instruction_acknowledge(message: types.Message, state: FSMContext):
    await safe_delete_message(message.chat.id, message.message_id)
    data = await state.get_data()
    if 'last_bot_msg_id' in data:
        await safe_delete_message(message.chat.id, data['last_bot_msg_id'])
    await message.answer("Оцените каждое состояние от 1 до 5.")
    await Survey.panas1.set()
    await send_panas(message, state, 'panas1', 0)


@dp.message_handler(lambda m: m.text == "Всё, посмотрел", state=Survey.video_watched)
async def video_watched_acknowledge(message: types.Message, state: FSMContext):
    await safe_delete_message(message.chat.id, message.message_id)
    data = await state.get_data()
    if 'last_bot_msg_id' in data:
        await safe_delete_message(message.chat.id, data['last_bot_msg_id'])
    await show_panas2_instruction(message, state)


@dp.message_handler(lambda m: m.text == "Понял", state=Survey.panas2_instruction)
async def panas2_instruction_acknowledge(message: types.Message, state: FSMContext):
    await safe_delete_message(message.chat.id, message.message_id)
    data = await state.get_data()
    if 'last_bot_msg_id' in data:
        await safe_delete_message(message.chat.id, data['last_bot_msg_id'])
    await message.answer("Оцените каждое состояние от 1 до 5.")
    await Survey.panas2.set()
    await send_panas(message, state, 'panas2', 0)


# === PANAS логика ===
async def send_panas(message: types.Message, state: FSMContext, step: str, index: int):
    if index >= len(PANAS_ITEMS):
        data = await state.get_data()
        scores = data.get(f'{step}_scores', [])
        pos_sum = sum(score for score, label in zip(scores, [item[1] for item in PANAS_ITEMS]) if label == "pos")
        neg_sum = sum(score for score, label in zip(scores, [item[1] for item in PANAS_ITEMS]) if label == "neg")
        await state.update_data(**{f'{step}_pos_sum': pos_sum, f'{step}_neg_sum': neg_sum})

        if step == 'panas1':
            group = data['group']
            if group == 1:
                await message.answer("Теперь посмотрите видео:")
                try:
                    await bot.send_video(message.chat.id, VIDEO_POSITIVE)
                    # await bot.send_sticker(message.chat.id, STICKER_ID)  # ← пример отправки стикера
                except Exception as e:
                    await message.answer("⚠️ Ошибка при отправке видео. Продолжаем без него.")
                new_msg_id = await send_and_track(message, "Когда закончите просмотр — нажмите кнопку ниже:",
                                                  video_watched_keyboard())
                await state.update_data(last_bot_msg_id=new_msg_id)
                await Survey.video_watched.set()
            elif group == 3:
                await message.answer("Теперь посмотрите видео:")
                try:
                    await bot.send_video(message.chat.id, VIDEO_NEGATIVE)
                except Exception as e:
                    await message.answer("⚠️ Ошибка при отправке видео. Продолжаем без него.")
                new_msg_id = await send_and_track(message, "Когда закончите просмотр — нажмите кнопку ниже:",
                                                  video_watched_keyboard())
                await state.update_data(last_bot_msg_id=new_msg_id)
                await Survey.video_watched.set()
            else:  # группа 2 — без видео и без PANAS-2
                await message.answer("Теперь оцените утверждения.")
                await Survey.statements.set()
                await send_statement(message, state, 0)
        else:
            await message.answer("Теперь оцените утверждения.")
            await Survey.statements.set()
            await send_statement(message, state, 0)
        return

    item_text, _ = PANAS_ITEMS[index]
    data = await state.get_data()
    if 'last_bot_msg_id' in data:
        await safe_delete_message(message.chat.id, data['last_bot_msg_id'])
    new_msg_id = await send_and_track(message, f"{item_text}:", rating_keyboard())
    await state.update_data(current_index=index, current_step=step, last_bot_msg_id=new_msg_id)


@dp.message_handler(lambda m: m.text in '12345', state=Survey.panas1)
async def panas1_resp(message: types.Message, state: FSMContext):
    await safe_delete_message(message.chat.id, message.message_id)
    data = await state.get_data()
    if 'last_bot_msg_id' in data:
        await safe_delete_message(message.chat.id, data['last_bot_msg_id'])
    score = int(message.text)
    idx = data['current_index']
    scores = data.get('panas1_scores', [])
    scores.append(score)
    await state.update_data(panas1_scores=scores)
    await send_panas(message, state, 'panas1', idx + 1)


@dp.message_handler(lambda m: m.text in '12345', state=Survey.panas2)
async def panas2_resp(message: types.Message, state: FSMContext):
    await safe_delete_message(message.chat.id, message.message_id)
    data = await state.get_data()
    if 'last_bot_msg_id' in data:
        await safe_delete_message(message.chat.id, data['last_bot_msg_id'])
    score = int(message.text)
    idx = data['current_index']
    scores = data.get('panas2_scores', [])
    scores.append(score)
    await state.update_data(panas2_scores=scores)
    await send_panas(message, state, 'panas2', idx + 1)


# === Функция: инструкция перед PANAS-2 ===
async def show_panas2_instruction(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if 'last_bot_msg_id' in data:
        await safe_delete_message(message.chat.id, data['last_bot_msg_id'])
    instruction_text = (
        "Теперь оцените ваше текущее эмоциональное состояние.\n\n"
        "Определите, насколько хорошо каждое из прилагательных описывает вас сейчас, "
        "по 5-балльной шкале:\n"
        "1 — совсем не согласен(а)\n"
        "5 — полностью согласен(а)"
    )
    new_msg_id = await send_and_track(message, instruction_text, understood_keyboard())
    await state.update_data(last_bot_msg_id=new_msg_id)
    await Survey.panas2_instruction.set()


# === Утверждения ===
async def send_statement(message: types.Message, state: FSMContext, index: int):
    if index >= len(STATEMENTS):
        await save_to_sheet(message, state)
        return
    stmt = STATEMENTS[index]
    data = await state.get_data()
    if 'last_bot_msg_id' in data:
        await safe_delete_message(message.chat.id, data['last_bot_msg_id'])
    new_msg_id = await send_and_track(message,
                                      f"Утв. {index + 1}/{len(STATEMENTS)}:\n\n{stmt['text']}\n\nВерите? (1–5)",
                                      rating_keyboard())
    await state.update_data(stmt_index=index, waiting_for_belief=True, last_bot_msg_id=new_msg_id)


@dp.message_handler(lambda m: m.text in '12345', state=Survey.statements)
async def stmt_resp(message: types.Message, state: FSMContext):
    await safe_delete_message(message.chat.id, message.message_id)
    data = await state.get_data()
    if 'last_bot_msg_id' in data:
        await safe_delete_message(message.chat.id, data['last_bot_msg_id'])
    if data.get('waiting_for_belief'):
        await state.update_data(waiting_for_belief=False, current_belief=int(message.text))
        new_msg_id = await send_and_track(message, "Уверенность? (1–5)", rating_keyboard())
        await state.update_data(last_bot_msg_id=new_msg_id)
    else:
        belief = data['current_belief']
        confidence = int(message.text)
        beliefs = data.get('beliefs', [])
        confidences = data.get('confidences', [])
        stmt_types = data.get('stmt_types', [])
        stmt_ids = data.get('stmt_ids', [])

        current_index = data['stmt_index']
        current_stmt = STATEMENTS[current_index]

        beliefs.append(belief)
        confidences.append(confidence)
        stmt_types.append(current_stmt['type'])
        stmt_ids.append(current_stmt['id'])

        await state.update_data(
            beliefs=beliefs,
            confidences=confidences,
            stmt_types=stmt_types,
            stmt_ids=stmt_ids,
            waiting_for_belief=True
        )
        await send_statement(message, state, data['stmt_index'] + 1)


# === Сохранение в Google Sheets ===
async def save_to_sheet(message: types.Message, state: FSMContext):
    data = await state.get_data()
    panas2_pos = data.get('panas2_pos_sum', "")
    panas2_neg = data.get('panas2_neg_sum', "")

    row = [
        data['user_id'],
        data.get('tg_username', 'нет'),
        data['gender'],
        data['age'],
        data['field'],
        data['group'],
        data['panas1_pos_sum'],
        data['panas1_neg_sum'],
        panas2_pos,
        panas2_neg
    ]

    beliefs = data.get('beliefs', [])
    confidences = data.get('confidences', [])
    stmt_types = data.get('stmt_types', [])
    stmt_ids = data.get('stmt_ids', [])

    for i in range(40):
        row.extend([
            stmt_ids[i] if i < len(stmt_ids) else "",
            stmt_types[i] if i < len(stmt_types) else "",
            beliefs[i] if i < len(beliefs) else "",
            confidences[i] if i < len(confidences) else ""
        ])

    SHEET.append_row(row)
    await message.answer(
        "Спасибо за участие! 🙏\n\nЕсли у вас есть пожелания, замечания или вопросы — напишите их здесь:")
    await state.update_data(last_bot_msg_id=None)  # не удаляем следующее сообщение
    await Survey.feedback.set()


# === Обратная связь ===
@dp.message(Survey.feedback)
async def handle_feedback(message: Message, state: FSMContext):
    feedback_text = message.text
    user_id = message.from_user.id
    username = message.from_user.username or "нет"

    try:
        # Отправляем тебе в Telegram
        await bot.send_message("@poniosch", f"💬 Обратная связь от {username} (ID: {user_id}):\n\n{feedback_text}")
        await message.answer("Спасибо за обратную связь! 💬")
    except Exception as e:
        await message.answer("⚠️ Не удалось отправить сообщение. Спасибо за ваше мнение!")

    await state.clear()

# === Вебхук ===
async def on_startup(bot: Bot) -> None:
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    logging.info(f"Webhook set to {WEBHOOK_URL}")

def main() -> None:
    app = web.Application()
    app.router.add_post("/webhook", SimpleRequestHandler(dispatcher=dp, bot=bot))
    setup_application(app, dp, bot=bot)
    web.run_app(app, host="0.0.0.0", port=PORT)

# Запуск
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()