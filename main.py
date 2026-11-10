import logging
import os
import asyncio
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

# Logging setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Credentials & Config
TOKEN = "9197059198:AAF-uRkXSJjGiQF54qsBXKBBfK53H9l5s3Q"
ADMIN_ID = 7458685213
ADMIN_USERNAME = "@nahidbro204"

# In-memory Database
user_balances = {}  # user_id -> balance

# Main Menu Keyboard
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("📥 জিমেইল কিনুন (Buy)", callback_data="buy_gmail")],
        [InlineKeyboardButton("📤 জিমেইল বিক্রি করুন (Sell)", callback_data="sell_gmail")],
        [InlineKeyboardButton("💰 ব্যালেন্স ও উইথড্র", callback_data="balance_menu")],
        [InlineKeyboardButton("☎️ এডমিন সাপোর্ট", url="https://t.me/nahidbro204")]
    ]
    return InlineKeyboardMarkup(keyboard)

# /start command
async def start(update: Update, context):
    user = update.effective_user
    if user.id not in user_balances:
        user_balances[user.id] = 0.0
        
    welcome_text = (
        f"আসসালামু আলাইকুম, {user.first_name}!\n\n"
        "আমাদের জিমেইল ট্রেডিং ও অটোমেটেড সার্ভিসে আপনাকে স্বাগতম।\n"
        "নিচের অপশন থেকে আপনার প্রয়োজনীয় সেবাটি বেছে নিন:"
    )
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=get_main_menu())
    elif update.callback_query:
        await update.callback_query.message.edit_text(welcome_text, reply_markup=get_main_menu())

# Callback Query Handler
async def button_handler(update: Update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "buy_gmail":
        text = "🛒 **জিমেইল ক্রয় প্যানেল:**\n\nপ্রতি জিমেইল এর মূল্য: ২০ BDT\nআপনি কি কিনতে চান?"
        keyboard = [
            [InlineKeyboardButton("✅ কনফার্ম কিনুন", callback_data="confirm_buy")],
            [InlineKeyboardButton("« মূল মেনু", callback_data="main_menu")]
        ]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "sell_gmail":
        text = "📤 **জিমেইল বিক্রি প্যানেল:**\n\nআপনার জিমেইল এর লগইন ডিটেইলস পাঠান অথবা এডমিনের সাথে যোগাযোগ করুন।"
        keyboard = [[InlineKeyboardButton("« মূল মেনু", callback_data="main_menu")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "balance_menu":
        balance = user_balances.get(user_id, 0.0)
        text = f"💰 **আপনার একাউন্ট:**\n\nবর্তমান ব্যালেন্স: {balance} BDT\n\n*(সর্বনিম্ন উইথড্র: ৬০ BDT)*"
        keyboard = [
            [InlineKeyboardButton("💸 উইথড্র করুন", callback_data="withdraw_request")],
            [InlineKeyboardButton("« মূল মেনু", callback_data="main_menu")]
        ]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "withdraw_request":
        balance = user_balances.get(user_id, 0.0)
        if balance < 60:
            await query.answer("⚠️ আপনার একাউন্টে পর্যাপ্ত ব্যালেন্স নেই! সর্বনিম্ন ৬০ BDT হতে হবে।", show_alert=True)
        else:
            text = f"💸 আপনার বর্তমান ব্যালেন্স {balance} BDT। উইথড্র করার জন্য আপনার পেমেন্ট নম্বর ও অ্যামাউন্ট লিখে পাঠান।"
            keyboard = [[InlineKeyboardButton("« মূল মেনু", callback_data="main_menu")]]
            await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "main_menu":
        await query.message.edit_text("প্রধান মেনু:", reply_markup=get_main_menu())

# Simple Aiohttp Web Server for Render Health Check
async def handle_web(request):
    return web.Response(text="Bot is running smoothly 24/7!")

async def run_web_server():
    app = web.Application()
    app.router.add_get("/", handle_web)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Web server started on port {port}")

async def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    await run_web_server()
    logger.info("Starting Telegram Bot...")
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    stop_event = asyncio.Event()
    await stop_event.wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
