import os
import logging
import asyncio
import yt_dlp
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# تنظیمات لاگ‌گرفتن
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# راه‌اندازی وب‌سرور کوچک برای پاسخ به پورت رایلوِی یا رندر
app_flask = Flask('')

@app_flask.route('/')
def home():
    return "Downloader Bot is alive and running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)

# خواندن توکن از متغیرهای محیطی
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("توکن ربات (BOT_TOKEN) در متغیرهای محیطی یافت نشد!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="📥 راهنمای دانلود", callback_data="help_download"),
        types.InlineKeyboardButton(text="📊 وضعیت ربات", callback_data="system_stats")
    )
    return builder.as_markup()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome_text = (
        f"سلام {message.from_user.first_name}! 🤖\n\n"
        "من ربات دانلودر شما روی سرور هستم.\n"
        "🔗 لینک ویدیوهای **اینستاگرام، تیک‌تاک یا پینترست** را بفرستید تا سریعاً دانلودشان کنم!"
    )
    await message.answer(welcome_text, reply_markup=get_main_menu())

@dp.callback_query(F.data == "help_download")
async def help_cb(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "💡 **راهنمای استفاده:**\n\n"
        "لینک پست یا ویدیو را در چت بفرستید.\n"
        "پشتیبانی فعال:\n"
        "▫️ اینستاگرام (Instagram)\n"
        "▫️ تیک‌تاک (TikTok)\n"
        "▫️ پینترست (Pinterest)",
        reply_markup=get_main_menu()
    )
    await callback.answer()

@dp.callback_query(F.data == "system_stats")
async def stats_cb(callback: types.CallbackQuery):
    await callback.message.edit_text("📊 وضعیت سرور: پایدار و آماده به کار 🟢", reply_markup=get_main_menu())
    await callback.answer()

@dp.message(F.text.regexp(r'https?://[^\s]+'))
async def download_video(message: types.Message):
    url = message.text.strip()
    
    if "youtube.com" in url or "youtu.be" in url:
        await message.answer("⚠️ دانلود از یوتیوب به دلیل محدودیت‌های امنیتی موقتاً غیرفعال است. لطفاً لینک **اینستاگرام یا تیک‌تاک** بفرستید.")
        return

    processing_msg = await message.answer("⏳ در حال دانلود ویدیو در سرور، لطفاً صبور باشید...")
    
    output_template = f"downloaded_video_{message.chat.id}.%(ext)s"
    ydl_opts = {
        'outtmpl': output_template,
        'format': 'mp4/best',
        'max_filesize': 50 * 1024 * 1024,
    }
    
    try:
        def run_dl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        filename = await asyncio.to_thread(run_dl)
        
        if filename and os.path.exists(filename):
            await message.answer_video(types.FSInputFile(filename), caption="✅ ویدیو با موفقیت دانلود شد!")
            try:
                os.remove(filename)
            except:
                pass
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
            except:
                pass
        else:
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
            except:
                pass
            await message.answer("❌ خطا در دانلود فایل. لطفاً لینک معتبر بفرستید.")
            
    except Exception as e:
        logging.error(f"Error: {e}")
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
        except:
            pass
        await message.answer("❌ خطایی رخ داد یا لینک نامعتبر است.")

@dp.message()
async def echo_other(message: types.Message):
    await message.answer("لطفاً یک **لینک معتبر** از اینستاگرام یا تیک‌تاک بفرستید.")

async def main():
    # استارت وب‌سرور در یک ترد جداگانه برای باز نگه داشتن پورت رایلوِی
    t = Thread(target=run_web)
    t.start()

    print("🤖 ربات دانلودر روی سرور روشن شد...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("❌ ربات متوقف شد.")
