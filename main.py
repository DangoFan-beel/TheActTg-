from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
import json
import asyncio
from config import TOKEN, ADMIN_ID

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

try:
    with open("users.json", "r") as f:
        users = json.load(f)
except:
    users = {}

try:
    with open("shop.json", "r") as f:
        shop = json.load(f)
except:
    shop = []

def save_users():
    with open("users.json", "w") as f:
        json.dump(users, f)

def save_shop():
    with open("shop.json", "w") as f:
        json.dump(shop, f)

def get_main_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("💰 Баланс", callback_data="balance"))
    kb.add(InlineKeyboardButton("🛒 Магазин", callback_data="shop"))
    return kb

def get_shop_keyboard():
    kb = InlineKeyboardMarkup()
    for item in shop:
        kb.add(InlineKeyboardButton(f"{item['name']} - {item['price']}", callback_data=f"buy_{item['id']}"))
    return kb

@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    user_id = str(msg.from_user.id)
    if user_id not in users:
        users[user_id] = {"balance": 100, "username": msg.from_user.username}
        save_users()
    await msg.answer("Привет! Используй кнопки ниже ⬇️", reply_markup=get_main_keyboard())

@dp.callback_query_handler(lambda c: True)
async def callback_handler(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)
    if user_id not in users:
        users[user_id] = {"balance": 100, "username": callback.from_user.username}
        save_users()

    if callback.data == "balance":
        await callback.message.answer(f"💰 Ваш баланс: {users[user_id]['balance']}")
    elif callback.data == "shop":
        if not shop:
            await callback.message.answer("Магазин пуст.")
        else:
            await callback.message.answer("🛒 Доступные товары:", reply_markup=get_shop_keyboard())
    elif callback.data.startswith("buy_"):
        item_id = int(callback.data.split("_")[1])
        item = next((x for x in shop if x["id"] == item_id), None)
        if item:
            if users[user_id]["balance"] >= item["price"]:
                users[user_id]["balance"] -= item["price"]
                save_users()
                await callback.message.answer(f"✅ Вы купили: {item['name']}")
                await bot.send_message(ADMIN_ID, f"🔔 @{callback.from_user.username} купил товар: {item['name']}")
            else:
                await callback.message.answer("❌ Недостаточно средств.")
        else:
            await callback.message.answer("❌ Товар не найден.")

@dp.message_handler(commands=["users"])
async def list_users(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return
    text = "📋 Пользователи:
"
    for uid, data in users.items():
        text += f"{uid} (@{data.get('username', 'нет username')}): {data['balance']} монет
"
    await msg.answer(text)

@dp.message_handler(commands=["add"])
async def add_balance(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return
    try:
        _, user_id, amount = msg.text.split()
        user_id = str(user_id)
        amount = int(amount)
        users[user_id]["balance"] += amount
        save_users()
        await msg.answer("✅ Баланс обновлён.")
    except:
        await msg.answer("❌ Ошибка. Используй /add user_id amount")

@dp.message_handler(commands=["newitem"])
async def new_item(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return
    try:
        _, name, price = msg.text.split()
        price = int(price)
        item_id = max([x["id"] for x in shop], default=0) + 1
        shop.append({"id": item_id, "name": name, "price": price})
        save_shop()
        await msg.answer("✅ Товар добавлен.")
    except:
        await msg.answer("❌ Ошибка. Используй /newitem Название Цена")

if __name__ == "__main__":
    executor.start_polling(dp)
