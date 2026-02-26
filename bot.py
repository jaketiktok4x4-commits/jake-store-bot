import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = "8534364815:AAGcK0WoAo7P41xIw0Qa3Q1j6BL473QenlE"
ADMIN_ID = 7196224715
CHANNEL_USERNAME = "t.me/jakestore_sd"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ------------------ Database ------------------

async def init_db():
    async with aiosqlite.connect("store.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            service TEXT,
            details TEXT,
            status TEXT DEFAULT 'Pending'
        )
        """)
        await db.commit()

# ------------------ Subscription Check ------------------

async def check_subscription(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ------------------ Main Menu ------------------

def main_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="💰 العملات والدفع الإلكتروني", callback_data="cat_payment")
    kb.button(text="🎮 شحن الألعاب", callback_data="cat_games")
    kb.button(text="📱 خدمات السوشيال", callback_data="cat_social")
    kb.button(text="📺 الاشتراكات الرقمية", callback_data="cat_subs")
    kb.button(text="🌍 السفر والتأشيرات", callback_data="cat_travel")
    kb.adjust(1)
    return kb.as_markup()

# ------------------ Start ------------------

@dp.message(CommandStart())
async def start(message: Message):
    if not await check_subscription(message.from_user.id):
        join_btn = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="اشترك في القناة", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")],
            [InlineKeyboardButton(text="تحقق", callback_data="check_sub")]
        ])
        await message.answer("⚠️ لازم تشترك في القناة أولاً", reply_markup=join_btn)
        return
    
    await message.answer("مرحباً بك في متجر الخدمات 👋\nاختر القسم:", reply_markup=main_menu())

# ------------------ Check Button ------------------

@dp.callback_query(F.data == "check_sub")
async def check_sub(callback: CallbackQuery):
    if await check_subscription(callback.from_user.id):
        await callback.message.edit_text("تم التحقق ✅\nاختر القسم:", reply_markup=main_menu())
    else:
        await callback.answer("لسه ما اشتركت ❌", show_alert=True)

# ------------------ Categories ------------------

services = {
    "cat_payment": [
        "بيع وشراء USDT",
        "PayPal إرسال/استلام",
        "Payeer",
        "الدفع للمواقع"
    ],
    "cat_games": [
        "شحن ببجي",
        "شحن فري فاير",
        "شحن Call of Duty",
        "شحن Game Pass"
    ],
    "cat_social": [
        "متابعين انستقرام",
        "متابعين تيك توك",
        "شحن نجوم تيليجرام"
    ],
    "cat_subs": [
        "Netflix",
        "beINSPORT",
        "Play Pass"
    ],
    "cat_travel": [
        "قطع تذاكر طيران",
        "استخراج تأشيرات"
    ]
}

@dp.callback_query(F.data.startswith("cat_"))
async def show_services(callback: CallbackQuery):
    category = callback.data
    kb = InlineKeyboardBuilder()
    
    for service in services[category]:
        kb.button(text=service, callback_data=f"order|{service}")
    
    kb.button(text="🔙 رجوع", callback_data="back")
    kb.adjust(1)
    
    await callback.message.edit_text("اختر الخدمة:", reply_markup=kb.as_markup())

# ------------------ Back ------------------

@dp.callback_query(F.data == "back")
async def back(callback: CallbackQuery):
    await callback.message.edit_text("اختر القسم:", reply_markup=main_menu())

# ------------------ Order ------------------

@dp.callback_query(F.data.startswith("order|"))
async def create_order(callback: CallbackQuery):
    service = callback.data.split("|")[1]
    
    await callback.message.answer(f"✍️ أرسل تفاصيل طلبك لخدمة:\n{service}")
    
    @dp.message()
    async def receive_details(message: Message):
        async with aiosqlite.connect("store.db") as db:
            await db.execute(
                "INSERT INTO orders (user_id, service, details) VALUES (?, ?, ?)",
                (message.from_user.id, service, message.text)
            )
            await db.commit()
        
        await bot.send_message(
            ADMIN_ID,
            f"طلب جديد 🔔\nالخدمة: {service}\nمن: {message.from_user.id}\nالتفاصيل:\n{message.text}"
        )
        
        await message.answer("✅ تم استلام طلبك وسيتم التواصل معك قريباً")

# ------------------ Run ------------------

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
