import asyncio
import logging
import os
import re
import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

BOT_TOKEN = os.getenv("BOT_TOKEN", "8700735340:AAHTpG2Q92WSC0JCW_rwgnlFhWWCZ-JfLmU")
ADMIN_IDS = {8119892612}  # admin telegram ID ni shu yerga yozing
PRICE_PER_KG = 15000
CARD_NUMBER = "5614 6812 5616 8760"
DB_NAME = "fayz_dunyo_cargo.db"

REGIONS = [
    "Toshkent shahar",
    "Toshkent viloyati",
    "Namangan viloyati",
    "Andijon viloyati",
    "Farg'ona viloyati",
]

LANG_LABELS = {
    "uz": "🇺🇿 O'zbekcha",
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
}

TEXTS: Dict[str, Dict[str, str]] = {
    "uz": {
        "welcome": "✨ <b>Assalomu alaykum!</b>\n\nFayz Dunyo cargo botiga xush kelibsiz.",
        "choose_lang": "🌐 Tilni tanlang:",
        "lang_changed": "✅ Til muvaffaqiyatli o'zgartirildi.",
        "menu_title": "🏠 <b>Asosiy menyu</b>\nKerakli bo'limni tanlang:",
        "new_order": "📦 Yangi buyurtma",
        "address": "📍 Manzillar",
        "payment": "💳 To'lov",
        "change_lang": "🌐 Til",
        "admin_panel": "🛠 Admin panel",
        "back_menu": "⬅️ Asosiy menyu",
        "enter_name": "📝 Ismingizni kiriting:",
        "enter_surname": "📝 Familiyangizni kiriting:",
        "enter_phone": "📱 Telefon raqamingizni yuboring yoki kiriting.\n\nMasalan: <code>+998901234567</code>",
        "share_phone": "📲 Raqamni yuborish",
        "choose_from": "🚚 Qaysi viloyatdan olib ketish kerak?",
        "choose_to": "📍 Qaysi viloyatga yuboriladi?",
        "enter_weight": "⚖️ Yuk og'irligini kiriting (kg).\n\nMasalan: <code>2</code> yoki <code>3.5</code>",
        "invalid_phone": "❌ Telefon raqami noto'g'ri.\nNamuna: <code>+998901234567</code>",
        "invalid_weight": "❌ Kg noto'g'ri kiritildi. Faqat son kiriting.",
        "same_region": "⚠️ Jo'natish va qabul qilish viloyati bir xil bo'lmasligi kerak.",
        "order_saved": "✅ Buyurtmangiz qabul qilindi.",
        "receipt": "🧾 <b>AVTO CHEK</b>\n\n<b>Buyurtma ID:</b> <code>{order_id}</code>\n<b>Ism:</b> {name}\n<b>Familiya:</b> {surname}\n<b>Telefon:</b> {phone}\n<b>Qayerdan:</b> {from_region}\n<b>Qayerga:</b> {to_region}\n<b>Og'irligi:</b> {weight} kg\n<b>1 kg narx:</b> {price_per_kg:,} so'm\n<b>Jami:</b> {total:,} so'm\n\nTo'lov uchun <b>💳 To'lov</b> bo'limidan foydalaning.",
        "address_text": "📍 <b>Xizmat ko'rsatish hududlari</b>\n\n• Toshkent shahar\n• Toshkent viloyati\n• Namangan viloyati\n• Andijon viloyati\n• Farg'ona viloyati",
        "payment_text": "💳 <b>To'lov usullari</b>\n\n<b>Click:</b> <code>{card}</code>\n<b>Payme:</b> <code>{card}</code>\n<b>Uzum Bank:</b> <code>{card}</code>",
        "admin_only": "⛔ Bu bo'lim faqat admin uchun.",
        "admin_title": "🛠 <b>Admin panel</b>",
        "admin_orders": "📦 Buyurtmalar",
        "admin_stats": "📊 Statistika",
        "admin_users": "👥 Foydalanuvchilar",
        "no_orders": "📭 Hozircha buyurtmalar yo'q.",
        "stats": "📊 <b>Statistika</b>\n\n<b>Foydalanuvchilar:</b> {users}\n<b>Buyurtmalar:</b> {orders}\n<b>Jami summa:</b> {total:,} so'm",
        "users_count": "👥 <b>Jami foydalanuvchilar:</b> {users}",
        "last_orders_title": "📦 <b>Oxirgi buyurtmalar</b>",
        "order_line": "\n<b>{n}.</b> <code>{order_id}</code> | {name} {surname} | {weight} kg | {total:,} so'm",
    },
    "ru": {
        "welcome": "✨ <b>Здравствуйте!</b>\n\nДобро пожаловать в cargo-бот Fayz Dunyo.",
        "choose_lang": "🌐 Выберите язык:",
        "lang_changed": "✅ Язык успешно изменён.",
        "menu_title": "🏠 <b>Главное меню</b>\nВыберите нужный раздел:",
        "new_order": "📦 Новый заказ",
        "address": "📍 Адреса",
        "payment": "💳 Оплата",
        "change_lang": "🌐 Язык",
        "admin_panel": "🛠 Админ панель",
        "back_menu": "⬅️ Главное меню",
        "enter_name": "📝 Введите имя:",
        "enter_surname": "📝 Введите фамилию:",
        "enter_phone": "📱 Отправьте или введите номер телефона.\n\nПример: <code>+998901234567</code>",
        "share_phone": "📲 Отправить номер",
        "choose_from": "🚚 Откуда нужно забрать?",
        "choose_to": "📍 Куда отправить?",
        "enter_weight": "⚖️ Введите вес груза в кг.\n\nНапример: <code>2</code> или <code>3.5</code>",
        "invalid_phone": "❌ Неверный номер телефона.",
        "invalid_weight": "❌ Вес введён неверно. Введите только число.",
        "same_region": "⚠️ Регион отправки и получения не должны совпадать.",
        "order_saved": "✅ Ваш заказ принят.",
        "receipt": "🧾 <b>АВТО ЧЕК</b>\n\n<b>ID заказа:</b> <code>{order_id}</code>\n<b>Имя:</b> {name}\n<b>Фамилия:</b> {surname}\n<b>Телефон:</b> {phone}\n<b>Откуда:</b> {from_region}\n<b>Куда:</b> {to_region}\n<b>Вес:</b> {weight} кг\n<b>Цена за 1 кг:</b> {price_per_kg:,} сум\n<b>Итого:</b> {total:,} сум",
        "address_text": "📍 <b>Регионы обслуживания</b>\n\n• Ташкент город\n• Ташкентская область\n• Наманганская область\n• Андижанская область\n• Ферганская область",
        "payment_text": "💳 <b>Способы оплаты</b>\n\n<b>Click:</b> <code>{card}</code>\n<b>Payme:</b> <code>{card}</code>\n<b>Uzum Bank:</b> <code>{card}</code>",
        "admin_only": "⛔ Этот раздел только для администратора.",
        "admin_title": "🛠 <b>Админ панель</b>",
        "admin_orders": "📦 Заказы",
        "admin_stats": "📊 Статистика",
        "admin_users": "👥 Пользователи",
        "no_orders": "📭 Заказов пока нет.",
        "stats": "📊 <b>Статистика</b>\n\n<b>Пользователи:</b> {users}\n<b>Заказы:</b> {orders}\n<b>Общая сумма:</b> {total:,} сум",
        "users_count": "👥 <b>Всего пользователей:</b> {users}",
        "last_orders_title": "📦 <b>Последние заказы</b>",
        "order_line": "\n<b>{n}.</b> <code>{order_id}</code> | {name} {surname} | {weight} кг | {total:,} сум",
    },
    "en": {
        "welcome": "✨ <b>Hello!</b>\n\nWelcome to Fayz Dunyo cargo bot.",
        "choose_lang": "🌐 Choose a language:",
        "lang_changed": "✅ Language updated successfully.",
        "menu_title": "🏠 <b>Main menu</b>\nPlease choose a section:",
        "new_order": "📦 New order",
        "address": "📍 Locations",
        "payment": "💳 Payment",
        "change_lang": "🌐 Language",
        "admin_panel": "🛠 Admin panel",
        "back_menu": "⬅️ Main menu",
        "enter_name": "📝 Enter your name:",
        "enter_surname": "📝 Enter your surname:",
        "enter_phone": "📱 Send or type your phone number.\n\nExample: <code>+998901234567</code>",
        "share_phone": "📲 Share phone",
        "choose_from": "🚚 From which region should we pick up?",
        "choose_to": "📍 To which region should we deliver?",
        "enter_weight": "⚖️ Enter cargo weight in kg.\n\nExample: <code>2</code> or <code>3.5</code>",
        "invalid_phone": "❌ Invalid phone number.",
        "invalid_weight": "❌ Invalid weight. Please enter a number only.",
        "same_region": "⚠️ Pickup and destination regions cannot be the same.",
        "order_saved": "✅ Your order has been received.",
        "receipt": "🧾 <b>AUTO RECEIPT</b>\n\n<b>Order ID:</b> <code>{order_id}</code>\n<b>Name:</b> {name}\n<b>Surname:</b> {surname}\n<b>Phone:</b> {phone}\n<b>From:</b> {from_region}\n<b>To:</b> {to_region}\n<b>Weight:</b> {weight} kg\n<b>Price per 1 kg:</b> {price_per_kg:,} UZS\n<b>Total:</b> {total:,} UZS",
        "address_text": "📍 <b>Service regions</b>\n\n• Tashkent city\n• Tashkent region\n• Namangan region\n• Andijan region\n• Fergana region",
        "payment_text": "💳 <b>Payment methods</b>\n\n<b>Click:</b> <code>{card}</code>\n<b>Payme:</b> <code>{card}</code>\n<b>Uzum Bank:</b> <code>{card}</code>",
        "admin_only": "⛔ This section is for admins only.",
        "admin_title": "🛠 <b>Admin panel</b>",
        "admin_orders": "📦 Orders",
        "admin_stats": "📊 Statistics",
        "admin_users": "👥 Users",
        "no_orders": "📭 No orders yet.",
        "stats": "📊 <b>Statistics</b>\n\n<b>Users:</b> {users}\n<b>Orders:</b> {orders}\n<b>Total amount:</b> {total:,} UZS",
        "users_count": "👥 <b>Total users:</b> {users}",
        "last_orders_title": "📦 <b>Latest orders</b>",
        "order_line": "\n<b>{n}.</b> <code>{order_id}</code> | {name} {surname} | {weight} kg | {total:,} UZS",
    },
}

class OrderState(StatesGroup):
    waiting_name = State()
    waiting_surname = State()
    waiting_phone = State()
    waiting_from_region = State()
    waiting_to_region = State()
    waiting_weight = State()


def db_connect():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, full_name TEXT, phone TEXT, lang TEXT DEFAULT 'uz', created_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT UNIQUE, user_id INTEGER, name TEXT, surname TEXT, phone TEXT, from_region TEXT, to_region TEXT, weight REAL, total INTEGER, created_at TEXT)")
    conn.commit()
    conn.close()


def upsert_user(user_id: int, full_name: str, lang: str = "uz", phone: str = ""):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE users SET full_name = ?, lang = ?, phone = COALESCE(NULLIF(?, ''), phone) WHERE user_id = ?", (full_name, lang, phone, user_id))
    else:
        cur.execute("INSERT INTO users (user_id, full_name, phone, lang, created_at) VALUES (?, ?, ?, ?, ?)", (user_id, full_name, phone, lang, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_user_lang(user_id: int) -> str:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else "uz"


def update_user_lang(user_id: int, lang: str):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("UPDATE users SET lang = ? WHERE user_id = ?", (lang, user_id))
    conn.commit()
    conn.close()


def save_order(data: dict) -> str:
    conn = db_connect()
    cur = conn.cursor()
    order_id = f"FD-{int(datetime.now().timestamp())}"
    cur.execute(
        "INSERT INTO orders (order_id, user_id, name, surname, phone, from_region, to_region, weight, total, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (order_id, data['user_id'], data['name'], data['surname'], data['phone'], data['from_region'], data['to_region'], data['weight'], data['total'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    conn.close()
    return order_id


def get_stats() -> Tuple[int, int, int]:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*), COALESCE(SUM(total), 0) FROM orders")
    orders, total = cur.fetchone()
    conn.close()
    return users, orders, total


def get_last_orders(limit: int = 10) -> List[tuple]:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT order_id, name, surname, weight, total FROM orders ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


def tr(user_id: int, key: str) -> str:
    lang = get_user_lang(user_id)
    return TEXTS.get(lang, TEXTS['uz'])[key]


def lang_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, label in LANG_LABELS.items():
        builder.button(text=label, callback_data=f"lang:{code}")
    builder.adjust(1)
    return builder.as_markup()


def main_menu_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=tr(user_id, 'new_order'))
    builder.button(text=tr(user_id, 'address'))
    builder.button(text=tr(user_id, 'payment'))
    builder.button(text=tr(user_id, 'change_lang'))
    if user_id in ADMIN_IDS:
        builder.button(text=tr(user_id, 'admin_panel'))
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)


def regions_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for region in REGIONS:
        builder.button(text=region)
    builder.button(text=tr(user_id, 'back_menu'))
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup(resize_keyboard=True)


def phone_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=tr(user_id, 'share_phone'), request_contact=True)],
            [KeyboardButton(text=tr(user_id, 'back_menu'))],
        ],
        resize_keyboard=True,
    )


def admin_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=tr(user_id, 'admin_orders'))
    builder.button(text=tr(user_id, 'admin_stats'))
    builder.button(text=tr(user_id, 'admin_users'))
    builder.button(text=tr(user_id, 'back_menu'))
    builder.adjust(2, 1, 1)
    return builder.as_markup(resize_keyboard=True)


def normalize_phone(phone: str) -> str:
    phone = phone.strip().replace(' ', '')
    if re.fullmatch(r'\+998\d{9}', phone):
        return phone
    if re.fullmatch(r'998\d{9}', phone):
        return '+' + phone
    return ''


def fmt_weight(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else str(value)


bot = Bot(BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())


async def show_menu(message: Message):
    await message.answer(tr(message.from_user.id, 'menu_title'), reply_markup=main_menu_keyboard(message.from_user.id))


@dp.message(CommandStart())
async def start_cmd(message: Message, state: FSMContext):
    await state.clear()
    upsert_user(message.from_user.id, message.from_user.full_name, 'uz')
    await message.answer(TEXTS['uz']['welcome'] + "\n\n" + TEXTS['uz']['choose_lang'], reply_markup=lang_keyboard())


@dp.callback_query(F.data.startswith('lang:'))
async def language_set(callback: CallbackQuery):
    lang = callback.data.split(':', 1)[1]
    upsert_user(callback.from_user.id, callback.from_user.full_name, lang)
    await callback.message.edit_text(TEXTS[lang]['welcome'])
    await callback.message.answer(TEXTS[lang]['menu_title'], reply_markup=main_menu_keyboard(callback.from_user.id))
    await callback.answer(TEXTS[lang]['lang_changed'])


@dp.message(F.text.in_([TEXTS[x]['change_lang'] for x in TEXTS]))
async def change_lang(message: Message):
    await message.answer(tr(message.from_user.id, 'choose_lang'), reply_markup=lang_keyboard())


@dp.message(F.text.in_([TEXTS[x]['address'] for x in TEXTS]))
async def address_handler(message: Message):
    await message.answer(tr(message.from_user.id, 'address_text'), reply_markup=main_menu_keyboard(message.from_user.id))


@dp.message(F.text.in_([TEXTS[x]['payment'] for x in TEXTS]))
async def payment_handler(message: Message):
    await message.answer(tr(message.from_user.id, 'payment_text').format(card=CARD_NUMBER), reply_markup=main_menu_keyboard(message.from_user.id))


@dp.message(F.text.in_([TEXTS[x]['new_order'] for x in TEXTS]))
async def new_order_handler(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(OrderState.waiting_name)
    await message.answer(tr(message.from_user.id, 'enter_name'))


@dp.message(OrderState.waiting_name)
async def get_name(message: Message, state: FSMContext):
    if message.text == tr(message.from_user.id, 'back_menu'):
        await state.clear()
        await show_menu(message)
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(OrderState.waiting_surname)
    await message.answer(tr(message.from_user.id, 'enter_surname'))


@dp.message(OrderState.waiting_surname)
async def get_surname(message: Message, state: FSMContext):
    if message.text == tr(message.from_user.id, 'back_menu'):
        await state.clear()
        await show_menu(message)
        return
    await state.update_data(surname=message.text.strip())
    await state.set_state(OrderState.waiting_phone)
    await message.answer(tr(message.from_user.id, 'enter_phone'), reply_markup=phone_keyboard(message.from_user.id))


@dp.message(OrderState.waiting_phone, F.contact)
async def get_phone_contact(message: Message, state: FSMContext):
    phone = normalize_phone(message.contact.phone_number)
    await state.update_data(phone=phone)
    await state.set_state(OrderState.waiting_from_region)
    await message.answer(tr(message.from_user.id, 'choose_from'), reply_markup=regions_keyboard(message.from_user.id))


@dp.message(OrderState.waiting_phone)
async def get_phone_text(message: Message, state: FSMContext):
    if message.text == tr(message.from_user.id, 'back_menu'):
        await state.clear()
        await show_menu(message)
        return
    phone = normalize_phone(message.text)
    if not phone:
        await message.answer(tr(message.from_user.id, 'invalid_phone'))
        return
    await state.update_data(phone=phone)
    await state.set_state(OrderState.waiting_from_region)
    await message.answer(tr(message.from_user.id, 'choose_from'), reply_markup=regions_keyboard(message.from_user.id))


@dp.message(OrderState.waiting_from_region)
async def get_from_region(message: Message, state: FSMContext):
    if message.text == tr(message.from_user.id, 'back_menu'):
        await state.clear()
        await show_menu(message)
        return
    if message.text not in REGIONS:
        await message.answer(tr(message.from_user.id, 'choose_from'), reply_markup=regions_keyboard(message.from_user.id))
        return
    await state.update_data(from_region=message.text)
    await state.set_state(OrderState.waiting_to_region)
    await message.answer(tr(message.from_user.id, 'choose_to'), reply_markup=regions_keyboard(message.from_user.id))


@dp.message(OrderState.waiting_to_region)
async def get_to_region(message: Message, state: FSMContext):
    if message.text == tr(message.from_user.id, 'back_menu'):
        await state.clear()
        await show_menu(message)
        return
    if message.text not in REGIONS:
        await message.answer(tr(message.from_user.id, 'choose_to'), reply_markup=regions_keyboard(message.from_user.id))
        return
    data = await state.get_data()
    if data.get('from_region') == message.text:
        await message.answer(tr(message.from_user.id, 'same_region'))
        return
    await state.update_data(to_region=message.text)
    await state.set_state(OrderState.waiting_weight)
    await message.answer(tr(message.from_user.id, 'enter_weight'))


@dp.message(OrderState.waiting_weight)
async def get_weight(message: Message, state: FSMContext):
    if message.text == tr(message.from_user.id, 'back_menu'):
        await state.clear()
        await show_menu(message)
        return
    try:
        weight = float(message.text.replace(',', '.'))
        if weight <= 0:
            raise ValueError
    except ValueError:
        await message.answer(tr(message.from_user.id, 'invalid_weight'))
        return

    data = await state.get_data()
    total = int(weight * PRICE_PER_KG)
    order_payload = {
        'user_id': message.from_user.id,
        'name': data['name'],
        'surname': data['surname'],
        'phone': data['phone'],
        'from_region': data['from_region'],
        'to_region': data['to_region'],
        'weight': weight,
        'total': total,
    }
    order_id = save_order(order_payload)

    await message.answer(tr(message.from_user.id, 'order_saved'))
    await message.answer(
        tr(message.from_user.id, 'receipt').format(
            order_id=order_id,
            name=order_payload['name'],
            surname=order_payload['surname'],
            phone=order_payload['phone'],
            from_region=order_payload['from_region'],
            to_region=order_payload['to_region'],
            weight=fmt_weight(weight),
            price_per_kg=PRICE_PER_KG,
            total=total,
        ),
        reply_markup=main_menu_keyboard(message.from_user.id),
    )

    admin_text = (
        f"📥 <b>Yangi buyurtma</b>\n\n"
        f"<b>ID:</b> <code>{order_id}</code>\n"
        f"<b>Mijoz:</b> {order_payload['name']} {order_payload['surname']}\n"
        f"<b>Telefon:</b> {order_payload['phone']}\n"
        f"<b>Qayerdan:</b> {order_payload['from_region']}\n"
        f"<b>Qayerga:</b> {order_payload['to_region']}\n"
        f"<b>Og'irlik:</b> {fmt_weight(weight)} kg\n"
        f"<b>Jami:</b> {total:,} so'm"
    )
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_text)
        except Exception:
            pass
    await state.clear()


@dp.message(F.text.in_([TEXTS[x]['admin_panel'] for x in TEXTS]))
async def admin_panel_handler(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer(tr(message.from_user.id, 'admin_only'))
        return
    await message.answer(tr(message.from_user.id, 'admin_title'), reply_markup=admin_keyboard(message.from_user.id))


@dp.message(F.text.in_([TEXTS[x]['admin_stats'] for x in TEXTS]))
async def admin_stats_handler(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer(tr(message.from_user.id, 'admin_only'))
        return
    users, orders, total = get_stats()
    await message.answer(tr(message.from_user.id, 'stats').format(users=users, orders=orders, total=total), reply_markup=admin_keyboard(message.from_user.id))


@dp.message(F.text.in_([TEXTS[x]['admin_users'] for x in TEXTS]))
async def admin_users_handler(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer(tr(message.from_user.id, 'admin_only'))
        return
    users, _, _ = get_stats()
    await message.answer(tr(message.from_user.id, 'users_count').format(users=users), reply_markup=admin_keyboard(message.from_user.id))


@dp.message(F.text.in_([TEXTS[x]['admin_orders'] for x in TEXTS]))
async def admin_orders_handler(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer(tr(message.from_user.id, 'admin_only'))
        return
    orders = get_last_orders(10)
    if not orders:
        await message.answer(tr(message.from_user.id, 'no_orders'), reply_markup=admin_keyboard(message.from_user.id))
        return
    text = tr(message.from_user.id, 'last_orders_title')
    for i, row in enumerate(orders, 1):
        order_id, name, surname, weight, total = row
        text += tr(message.from_user.id, 'order_line').format(n=i, order_id=order_id, name=name, surname=surname, weight=fmt_weight(weight), total=total)
    await message.answer(text, reply_markup=admin_keyboard(message.from_user.id))


@dp.message(F.text.in_([TEXTS[x]['back_menu'] for x in TEXTS]))
async def back_handler(message: Message, state: FSMContext):
    await state.clear()
    await show_menu(message)


@dp.message(Command('menu'))
async def menu_command(message: Message, state: FSMContext):
    await state.clear()
    await show_menu(message)


@dp.message()
async def fallback(message: Message):
    await show_menu(message)


async def main():
    init_db()
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
