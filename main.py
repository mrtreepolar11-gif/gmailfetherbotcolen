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
            [InlineKeyboardButton("🟢 ফ্রেশ মেইল বিক্রি করুন (২০৳)", callback_data="sell_fresh")],
            [InlineKeyboardButton("🔵 টুএফ মেইল বিক্রি করুন (২৫৳)", callback_data="sell_2fa
