import logging
import os
import asyncio
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# Logging setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Credentials & Config
TOKEN = "9197059198:AAF-uRkXSJjGiQF54qsBXKBBfK53H9l5s3Q"
ADMIN_ID = 7458685213
ADMIN_USERNAME = "@nahidbro204"

# In-memory Database & States
user_balances = {}  # user_id -> balance
user_states = {}   # user_id -> state tracking
user_temp_data = {} # user_id -> temp data for selling/depositing

# Main Menu Keyboard
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("📥 জিমেইল কিনুন (Buy)", callback_data="buy_gmail")],
        [InlineKeyboardButton("📤 জিমেইল বিক্রি করুন (Sell)", callback_data="sell_gmail")],
        [InlineKeyboardButton("➕ ডিপোজিট করুন (Deposit)", callback_data="deposit_menu")],
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
    user_states.pop(user_id, None)

    if data == "buy_gmail":
        text = (
            "🛒 **জিমেইল ক্রয় প্যানেল:**\n\n"
            "প্রতি জিমেইল এর মূল্য: **৩০ BDT**\n\n"
            "জিমেইল কিনতে বা বিস্তারিত জানতে সরাসরি এডমিনের সাথে যোগাযোগ করুন:\n"
            f"☎️ এডমিন কন্টাক্ট: {ADMIN_USERNAME}"
        )
        keyboard = [
            [InlineKeyboardButton("☎️ এডমিনের সাথে কথা বলুন", url="https://t.me/nahidbro204")],
            [InlineKeyboardButton("« মূল মেনু", callback_data="main_menu")]
        ]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "sell_gmail":
        text = (
            "📤 **জিমেইল বিক্রি করার মূল্যতালিকা:**\n\n"
            "• ফ্রেশ মেইল: ২০ টাকা\n"
            "• টুএফ (2FA) মেইল: ২৫ টাকা\n"
            "• ইউজড মেইল: ১০ টাকা\n"
            "• ফেসবুক ক্রিয়েট মেইল: ১৫ টাকা\n\n"
            "আপনি কোন ক্যাটাগরির মেইল বিক্রি করতে চান?"
        )
        keyboard = [
            [InlineKeyboardButton("ফ্রেশ মেইল বিক্রি করুন (২০৳)", callback_data="sell_fresh")],
            [InlineKeyboardButton("টুএফ মেইল বিক্রি করুন (২৫৳)", callback_data="sell_2fa")],
            [InlineKeyboardButton("ইউজড মেইল বিক্রি করুন (১০৳)", callback_data="sell_used")],
            [InlineKeyboardButton("ফেসবুক ক্রিয়েট মেইল (১৫৳)", callback_data="sell_fb")],
            [InlineKeyboardButton("« মূল মেনু", callback_data="main_menu")]
        ]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "sell_fresh":
        text = "প্রতিটি ফ্রেশ জিমেইলের মূল্য ২০ টাকা করে আপনি বিক্রি করতে চাচ্ছেন?\n\nআপনি কি বিক্রি করতে চান?"
        keyboard = [
            [InlineKeyboardButton("হ্যাঁ (Yes)", callback_data="confirm_sell_fresh")],
            [InlineKeyboardButton("না (No)", callback_data="sell_gmail")]
        ]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "confirm_sell_fresh":
        user_states[user_id] = "waiting_fresh_email"
        text = "📩 অনুগ্রহ করে আপনার জিমেইল অ্যাকাউন্ট (ইমেইল) দিন:"
        keyboard = [[InlineKeyboardButton("« বাতিল", callback_data="sell_gmail")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data in ["sell_2fa", "sell_used", "sell_fb"]:
        text = "এই ক্যাটাগরির মেইল বিক্রির জন্য সরাসরি এডমিনের সাথে যোগাযোগ করুন:"
        keyboard = [
            [InlineKeyboardButton("☎️ এডমিন সাপোর্ট", url="https://t.me/nahidbro204")],
            [InlineKeyboardButton("« মূল মেনু", callback_data="main_menu")]
        ]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "deposit_menu":
        user_states[user_id] = "waiting_deposit"
        text = (
            "💳 **ডিপোজিট করার নিয়ম:**\n\n"
            "সর্বনিম্ন ডিপোজিট: **৬০ BDT**\n\n"
            "আমাদের মার্চেন্ট বিকাশ/নগদ নম্বরে টাকা পাঠিয়ে ট্রানজেকশন আইডি দিন:\n"
            "👉 নম্বর: `01715914270` (Personal)\n\n"
            "টাকা পাঠিয়ে আপনার **TrxID ও টাকার পরিমাণ** লিখে চ্যাটে পাঠান:"
        )
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
            await query.answer("⚠️ আপনার একাউন্টে পর্যাপ্ত ব্যালেন্স নেই! সর্বনিম্ন উইথড্র ৬০ BDT হতে হবে।", show_alert=True)
        else:
            user_states[user_id] = "waiting_withdraw"
            text = f"💸 আপনার বর্তমান ব্যালেন্স {balance} BDT। উইথড্র করার জন্য আপনার পেমেন্ট নম্বর (Bkash/Nagad) ও অ্যামাউন্ট লিখে পাঠান:"
            keyboard = [[InlineKeyboardButton("« মূল মেনু", callback_data="main_menu")]]
            await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "main_menu":
        await query.message.edit_text("প্রধান মেনু:", reply_markup=get_main_menu())

# Message Handler for multi-step inputs
async def handle_message(update: Update, context):
    user_id = update.effective_user.id
    text = update.message.text
    state = user_states.get(user_id)

    if state == "waiting_fresh_email":
        user_temp_data[user_id] = {"email": text}
        user_states[user_id] = "waiting_fresh_password"
        await update.message.reply_text("🔑 অনুগ্রহ করে জিমেইলের পাসওয়ার্ড দিন:")

    elif state == "waiting_fresh_password":
        email = user_temp_data.get(user_id, {}).get("email", "N/A")
        password = text
        
        await update.message.reply_text("✅ আপনার জিমেইল ও পাসওয়ার্ড সফলভাবে জমা হয়েছে! এডমিন চেক করে ব্যালেন্স আপডেট করে দেবেন।")
        
        # Notify Admin
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📤 **নতুন ফ্রেশ জিমেইল বিক্রি রিকোয়েস্ট!**\n\n👤 ইউজার আইডি: `{user_id}`\n📧 জিমেইল: `{email}`\n🔑 পাসওয়ার্ড: `{password}`",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")
            
        user_states.pop(user_id, None)
        user_temp_data.pop(user_id, None)
        await update.message.reply_text("প্রধান মেনু:", reply_markup=get_main_menu())

    elif state == "waiting_deposit":
        await update.message.reply_text("✅ আপনার ডিপোজিট রিকোয়েস্ট জমা হয়েছে! এডমিন চেক করে ব্যালেন্স অ্যাড করে দেবেন।")
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🔔 **নতুন ডিপোজিট রিকোয়েস্ট!**\n\n👤 ইউজার আইডি: `{user_id}`\n💬 বিবরণ: {text}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")
            
        user_states.pop(user_id, None)
        await update.message.reply_text("প্রধান মেনু:", reply_markup=get_main_menu())

    elif state == "waiting_withdraw":
        await update.message.reply_text("✅ আপনার উইথড্র রিকোয়েস্ট সফলভাবে জমা হয়েছে! এডমিন পেমেন্ট কমপ্লিট করে দেবেন।")
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"💸 **নতুন উইথড্র রিকোয়েস্ট!**\n\n👤 ইউজার আইডি: `{user_id}`\n💬 বিবরণ: {text}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")
            
        user_states.pop(user_id, None)
        await update.message.reply_text("প্রধান মেনু:", reply_markup=get_main_menu())

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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

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
