from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import sqlite3
from datetime import datetime, timedelta

bot = Bot(token='8429888941:AAEDvohMaiRkLNHw37JO_fZGZfi1L27ysSQ')
dp = Dispatcher(bot)

ADMIN_ID = 1341872330

# اتصال به دیتابیس
conn = sqlite3.connect('user.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, join_date TEXT)''')
conn.commit()

# هندلر شروع برای اضافه کردن کاربران
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id
    today_str = datetime.now().strftime('%Y-%m-%d')
    c.execute("INSERT OR IGNORE INTO users (user_id, join_date) VALUES (?, ?)", (user_id, today_str))
    conn.commit()
    await message.reply("خوش آمدید!")

# هندلر پنل ادمین
@dp.message_handler(commands=['admin'])
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("دسترسی غیر مجاز")
        return
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("آمار", callback_data='stats'))
    keyboard.add(InlineKeyboardButton("ارسال همگانی", callback_data='broadcast'))
    keyboard.add(InlineKeyboardButton("سفارشات", callback_data='orders'))
    keyboard.add(InlineKeyboardButton("محصولات", callback_data='products'))
    keyboard.add(InlineKeyboardButton("تنظیمات", callback_data='settings'))
    await message.reply("داشبورد ادمین", reply_markup=keyboard)

# هندلر آمار
@dp.callback_query_handler(lambda c: c.data == 'stats')
async def stats(callback_query: types.CallbackQuery):
    if callback_query.from_user.id != ADMIN_ID:
        await bot.answer_callback_query(callback_query.id, "دسترسی غیر مجاز")
        return
    today_str = datetime.now().strftime('%Y-%m-%d')
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    week_ago_str = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM users WHERE join_date = ?", (today_str,))
    today_users = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM users WHERE join_date = ?", (yesterday_str,))
    yesterday_users = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM users WHERE join_date >= ?", (week_ago_str,))
    week_users = c.fetchone()[0]
    
    # موجودی انبار و سفارشات فعلا 0 (می‌توانید بعدا پیاده‌سازی کنید)
    inventory = 0
    total_orders = 0
    
    text = f"تعداد کل کاربران: {total_users}\n"
    text += f"کاربران امروز اضافه شده: {today_users}\n"
    text += f"کاربران دیروز اضافه شده: {yesterday_users}\n"
    text += f"کاربران هفته گذشته اضافه شده: {week_users}\n"
    text += f"تعداد موجودی انبار: {inventory}\n"
    text += f"تعداد کل سفارشات: {total_orders}"
    
    await bot.send_message(callback_query.from_user.id, text)
    await bot.answer_callback_query(callback_query.id)

# کلاس برای استیت ارسال همگانی
class Broadcast(StatesGroup):
    message = State()

# شروع ارسال همگانی
@dp.callback_query_handler(lambda c: c.data == 'broadcast')
async def start_broadcast(callback_query: types.CallbackQuery):
    if callback_query.from_user.id != ADMIN_ID:
        await bot.answer_callback_query(callback_query.id, "دسترسی غیر مجاز")
        return
    await Broadcast.message.set()
    await bot.send_message(callback_query.from_user.id, "پیام خود را برای ارسال همگانی وارد کنید:")
    await bot.answer_callback_query(callback_query.id)

# پردازش پیام ارسال همگانی
@dp.message_handler(state=Broadcast.message)
async def process_broadcast(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await state.finish()
        return
    broadcast_message = message.text
    c.execute("SELECT user_id FROM users")
    users = c.fetchall()
    sent = 0
    failed = 0
    for user in users:
        try:
            await bot.send_message(user[0], broadcast_message)
            sent += 1
        except:
            failed += 1
    await message.reply(f"پیام به {sent} کاربر ارسال شد، {failed} شکست خورد.")
    await state.finish()

# هندلرهای placeholder برای بقیه دکمه‌ها
@dp.callback_query_handler(lambda c: c.data in ['orders', 'products', 'settings'])
async def placeholder(callback_query: types.CallbackQuery):
    if callback_query.from_user.id != ADMIN_ID:
        await bot.answer_callback_query(callback_query.id, "دسترسی غیر مجاز")
        return
    await bot.send_message(callback_query.from_user.id, "این بخش هنوز پیاده‌سازی نشده است.")
    await bot.answer_callback_query(callback_query.id)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)