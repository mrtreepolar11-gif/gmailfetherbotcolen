import logging
import os
import asyncio
from datetime import datetime, time
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatJoinRequest
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ChatJoinRequestHandler,
    filters,
)

# Logging setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Credentials & Config
TOKEN = "9197059198:AAF-uRkXSJjGiQF54qsBXKBBfK53H9l5s3Q"
ADMIN_ID = 7458685213
ADMIN_USERNAME = "@nahidbro204"
CHANNEL_LINK = "https://t.me/nahidgmailsallar204"
BOT_LINK = "https://t.me/gmailfetherbot"

GROUP_CHAT_ID = -100435225206  # আপনার গ্রুপ আইডি

# In-memory Database & States
user_balances = {}     # user_id -> balance
approved_users = set() # approved user IDs after joining channel
user_states = {}       # user_id -> state tracking
user_temp_data = {}    # user_id -> temp data storage (email, password, etc.)

# Main Menu Keyboard
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("📥 জিমেইল কিনুন (Buy)", callback_data="buy_gmail")],
        [InlineKeyboardButton("📤 জিমেইল বিক্রি করুন (Sell)", callback_data="sell_gmail")],
        [InlineKeyboardButton("➕ ডিপোজিট করুন (Deposit)", callback_data="deposit_menu")],
        [InlineKeyboardButton("💰 ব্যালেন্স ও উইথড্র", callback_data="balance_menu")],
        [InlineKeyboardButton("☎️ এডমিন সাপোর্ট & রিকভারি", url="https://t.me/nahidbro204")]
    ]
    return InlineKeyboardMarkup(keyboard)

# /start command (Checks channel approval)
async def start(update: Update, context):
    user = update.effective_user
    if user.id not in user_balances:
        user_balances[user.id] = 0.0

    if user.id == ADMIN_ID or user.id in approved_users:
        welcome_text = (
            f"আসসালামু আলাইকুম, {user.first_name}!\n\n"
            "আমাদের জিমেইল ট্রেডিং ও অটোমেটেড সার্ভিসে আপনাকে স্বাগতম।"
        )
        if update.message:
            await update.message.reply_text(welcome_text, reply_markup=get_main_menu())
        elif update.callback_query:
            await update.callback_query.message.edit_text(welcome_text, reply_markup=get_main_menu())
    else:
        text = (
            f"⚠️ বটটি ব্যবহার করতে হলে প্রথমে আমাদের অফিশিয়াল চ্যানেলে/গ্রুপে জয়েন করতে হবে!\n\n"
            f"👉 লিংকে ক্লিক করে জয়েন রিকোয়েস্ট পাঠান: {CHANNEL_LINK}\n\n"
            "জয়েন করার পর নিচের বাটনে ক্লিক করুন:"
        )
        keyboard = [[InlineKeyboardButton("✅ আমি জয়েন করেছি", callback_data="check_join")]]
        if update.message:
            await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        elif update.callback_query:
            await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# Check join button callback
async def check_join_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id in approved_users or user_id == ADMIN_ID:
        await query.message.edit_text("স্বাগতম! আপনার মেনু:", reply_markup=get_main_menu())
    else:
        await query.answer("⚠️ এডমিন এখনো আপনার চ্যানেল জয়েন রিকোয়েস্ট অ্যাপ্রুভ করেননি। দয়া করে অপেক্ষা করুন。", show_alert=True)

# Auto handle channel join requests and notify admin
async def handle_chat_join_request(update: ChatJoinRequest, context):
    user = update.from_user
    user_id = user.id

    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_user_{user_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_user_{user_id}")
        ]
    ]
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🔔 **নতুন চ্যানেল জয়েন রিকোয়েস্ট!**\n\n👤 নাম: {user.full_name}\n🆔 ইউজার আইডি: `{user_id}`\n🌐 ইউজারনেম: @{user.username if user.username else 'N/A'}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Failed to send join request to admin: {e}")

# Callback Query Handler
async def button_handler(update: Update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    user_states.pop(user_id, None)

    if data.startswith("approve_user_"):
        target_id = int(data.split("_")[2])
        approved_users.add(target_id)
        await query.message.edit_text(f"✅ ইউজার (`{target_id}`) এর রিকোয়েস্ট সফলভাবে **অ্যাপ্রুভ** করা হয়েছে。", parse_mode="Markdown")
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text="🎉 আপনার চ্যানেল জয়েন রিকোয়েস্ট অ্যাপ্রুভ করা হয়েছে! এখন আপনি বট ব্যবহার করতে পারবেন। /start লিখে মেনুতে যান。"
            )
        except Exception as e:
            logger.error(f"Failed to notify user: {e}")
        return

    elif data.startswith("reject_user_"):
        target_id = int(data.split("_")[2])
        await query.message.edit_text(f"❌ ইউজার (`{target_id}`) এর রিকোয়েস্ট **রিজেক্ট** করা হয়েছে。", parse_mode="Markdown")
        return

    if data.startswith("dep_approve_"):
        parts = data.split("_")
        target_id = int(parts[2])
        amount = float(parts[3])
        user_balances[target_id] = user_balances.get(target_id, 0.0) + amount
        await query.message.edit_text(f"✅ ডিপোজিট সফলভাবে **অ্যাপ্রুভ** করা হয়েছে। ইউজারের অ্যাকাউন্টে {amount} BDT যোগ হয়েছে。")
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=f"✅ আপনার {amount} BDT ডিপোজিট এডমিন কর্তৃক **অ্যাপ্রুভ** হয়েছে! আপনার বর্তমান ব্যালেন্স: {user_balances[target_id]} BDT。"
            )
        except Exception as e:
            logger.error(f"Failed to notify user: {e}")
        return

    elif data.startswith("dep_reject_"):
        target_id = int(data.split("_")[2])
        await query.message.edit_text("❌ ডিপোজিট রিকোয়েস্ট **রিজেক্ট** করা হয়েছে。")
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=" আপনার ডিপোজিট রিকোয়েস্টটি এডমিন কর্তৃক রিজেক্ট করা হয়েছে。"
            )
        except Exception as e:
            logger.error(f"Failed to notify user: {e}")
        return

    # New Admin Action Handlers for rejecting/approving Gmail submissions with user notification
    if data.startswith("gmail_reject_"):
        parts = data.split("_")
        target_id = int(parts[2])
        
        # Notify Admin Panel
        await query.message.edit_text("মিশনটি **রিজেক্ট** করা হয়েছে এবং ইউজারকে নোটিফিকেশন পাঠানো হয়েছে。")
        
        # Notify User Privately
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text="⚠️ **জরুরি নোটিফিকেশন:**\n\nদুঃখিত, আপনার সাবমিট করা জিমেইলটি সঠিক না হওয়ায় এডমিন কর্তৃক **রিজেক্ট** করা হয়েছে। দয়া করে পরবর্তী সময় থেকে জিমেইল সাবমিট করার আগে ভালো করে চেক করে সাবমিট করবেন। ধন্যবাদ।"
            )
        except Exception as e:
            logger.error(f"Failed to notify user about Gmail rejection: {e}")
        return

    elif data.startswith("gmail_approve_"):
        parts = data.split("_")
        target_id = int(parts[2])
        amount_to_add = float(parts[3])
        
        user_balances[target_id] = user_balances.get(target_id, 0.0) + amount_to_add
        await query.message.edit_text(f"✅ জিমেইল সাবমিশনটি **অ্যাপ্রুভ** করা হয়েছে। ইউজারের অ্যাকাউন্টে {amount_to_add} BDT যোগ করা হয়েছে。")
        
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=f"🎉 **অভিনন্দন!**\n\nআপনার সাবমিট করা জিমেইলটি সঠিক হওয়ায় এডমিন কর্তৃক **অ্যাপ্রুভ** করা হয়েছে এবং আপনার অ্যাকাউন্টে {amount_to_add} BDT যুক্ত করা হয়েছে।"
            )
        except Exception as e:
            logger.error(f"Failed to notify user about Gmail approval: {e}")
        return

    if data == "buy_gmail":
        user_states[user_id] = "waiting_buy_qty"
        text = (
            "🛒 **জিমেইল ক্রয় প্যানেল:**\n\n"
            "• প্রতি জিমেইল এর মূল্য: **৩০ BDT**\n"
            "• আপনি কয়টি জিমেইল কিনতে চান? সংখ্যাটি লিখে পাঠান (যেমন: `2` বা `5`):"
        )
        keyboard = [[InlineKeyboardButton("« মূল মেনু", callback_data="main_menu")]]
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
        text = f"এই ক্যাটাগরির মেইলের জন্য সরাসরি এডমিনের সাথে যোগাযোগ করুন:\n☎️ {ADMIN_USERNAME}"
        keyboard = [
            [InlineKeyboardButton("☎️ এডমিন সাপোর্ট", url="https://t.me/nahidbro204")],
            [InlineKeyboardButton("« মূল মেনু", callback_data="main_menu")]
        ]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "deposit_menu":
        user_states[user_id] = "waiting_deposit_amount"
        text = (
            "💳 **ডিপোজিট সিস্টেম:**\n\n"
            "আমাদের বিকাশ/নগদ পার্সোনাল নম্বর:\n"
            "👉 `01715914270`\n\n"
            "• সর্বনিম্ন ডিপোজিট: **৬০ BDT**\n\n"
            "আপনি কত টাকা ডিপোজিট করতে চান? সংখ্যাটি লিখে পাঠান (যেমন: `100`):"
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
            await query.answer("⚠️ আপনার একাউন্টে পর্যাপ্ত ব্যালেন্স নেই! সর্বনিম্ন উইথড্র ৬০ BDT হতে হবে。", show_alert=True)
        else:
            user_states[user_id] = "waiting_withdraw"
            text = f"💸 আপনার বর্তমান ব্যালেন্স {balance} BDT。 উইথড্র করার জন্য আপনার পেমেন্ট নম্বর ও অ্যামাউন্ট লিখে পাঠান:"
            keyboard = [[InlineKeyboardButton("« মূল মেনু", callback_data="main_menu")]]
            await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "main_menu":
        await query.message.edit_text("প্রধান মেনু:", reply_markup=get_main_menu())

# Message Handler for multi-step inputs
async def handle_message(update: Update, context):
    user_id = update.effective_user.id
    text = update.message.text
    state = user_states.get(user_id)

    if state == "waiting_buy_qty":
        try:
            qty = int(text)
            if qty <= 0:
                raise ValueError()
        except ValueError:
            await update.message.reply_text("⚠️ দয়া করে সঠিক সংখ্যা লিখুন (যেমন: 2, 3):")
            return

        total_cost = qty * 30
        current_balance = user_balances.get(user_id, 0.0)

        if current_balance >= total_cost:
            user_balances[user_id] = current_balance - total_cost
            user_states.pop(user_id, None)

            await update.message.reply_text(
                f"✅ সফলভাবে আপনার একাউন্ট থেকে {total_cost} BDT কেটে নেওয়া হয়েছে!\n"
                f"অবশিষ্ট ব্যালেন্স: {user_balances[user_id]} BDT\n\n"
                "⏳ অর্ডার স্ট্যাটাস: **পেন্ডিং**\n"
                "এডমিন খুব শীঘ্রই আপনাকে জিমেইলগুলো দিয়ে দেবেন。"
            )

            try:
                await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"🛒 **নতুন জিমেইল ক্রয় অর্ডার!**\n\n👤 ইউজার আইডি: `{user_id}`\n📦 পরিমাণ: {qty} টি\n💵 মোট মূল্য: {total_cost} BDT\n📌 স্ট্যাটাস: পেন্ডিং\n\nদয়া করে ইউজারকে জিমেইলগুলো প্রদান করুন এবং যোগাযোগ করুন: {ADMIN_USERNAME}",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Failed to notify admin: {e}")

            await update.message.reply_text("প্রধান মেনু:", reply_markup=get_main_menu())
        else:
            user_states.pop(user_id, None)
            await update.message.reply_text(
                f" পর্যাপ্ত ব্যালেন্স নেই!\n"
                f"আপনার প্রয়োজন {total_cost} BDT, কিন্তু আছে {current_balance} BDT。\n"
                "অনুগ্রহ করে আগে ডিপোজিট করুন。",
                reply_markup=get_main_menu()
            )

    elif state == "waiting_deposit_amount":
        try:
            amount = float(text)
            if amount < 60:
                await update.message.reply_text("⚠️ সর্বনিম্ন ডিপোজিট ৬০ BDT হতে হবে। আবার সঠিক পরিমাণ লিখুন:")
                return
        except ValueError:
            await update.message.reply_text("⚠️ দয়া করে সঠিক সংখ্যা লিখুন (যেমন: 100):")
            return

        user_temp_data[user_id] = {"deposit_amount": amount}
        user_states[user_id] = "waiting_deposit_trx"
        await update.message.reply_text(
            f"✅ ডিপোজিট অ্যামাউন্ট: {amount} BDT গৃহীত হয়েছে。\n\n"
            "🔑 এখন আপনার পেমেন্ট করা **ট্রানজেকশন আইডি (TrxID)** লিখে পাঠান:"
        )

    elif state == "waiting_deposit_trx":
        trx_id = text
        amount = user_temp_data.get(user_id, {}).get("deposit_amount", 0)

        await update.message.reply_text(
            "⏳ আপনার ডিপোজিট রিকোয়েস্ট জমা হয়েছে!\n"
            "স্ট্যাটাস: **পেন্ডিং**\n"
            "এডমিন চেক করে আপনার অ্যাকাউন্টে ব্যালেন্স যুক্ত করে দেবেন。"
        )

        keyboard = [
            [
                InlineKeyboardButton("✅ Approve Deposit", callback_data=f"dep_approve_{user_id}_{amount}"),
                InlineKeyboardButton("❌ Reject Deposit", callback_data=f"dep_reject_{user_id}")
            ]
        ]
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"💳 **নতুন ডিপোজিট রিকোয়েস্ট!**\n\n👤 ইউজার আইডি: `{user_id}`\n💵 অ্যামাউন্ট: {amount} BDT\n🔑 TrxID: `{trx_id}`\n📌 স্ট্যাটাস: পেন্ডিং",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")

        user_states.pop(user_id, None)
        user_temp_data.pop(user_id, None)
        await update.message.reply_text("প্রধান মেনু:", reply_markup=get_main_menu())

    elif state == "waiting_fresh_email":
        user_temp_data[user_id] = {"email": text}
        user_states[user_id] = "waiting_fresh_password"
        await update.message.reply_text("🔑 অনুগ্রহ করে জিমেইলের পাসওয়ার্ড দিন:")

    elif state == "waiting_fresh_password":
        email = user_temp_data.get(user_id, {}).get("email", "N/A")
        password = text

        await update.message.reply_text("✅ আপনার ফ্রেশ জিমেইল ও পাসওয়ার্ড সফলভাবে জমা হয়েছে! এডমিন চেক করে ব্যালেন্স আপডেট করে দেবেন。")

        # Admin Approval/Rejection buttons with dynamic user_id targeting
        admin_keyboard = [
            [
                InlineKeyboardButton("✅ Approve Email", callback_data=f"gmail_approve_{user_id}_20"), # 20 BDT assumed payment
                InlineKeyboardButton("", callback_data=f"gmail_reject_{user_id}")
            ]
        ]

        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📤 **নতুন ফ্রেশ জিমেইল বিক্রি রিকোয়েস্ট!**\n\n👤 ইউজার আইডি: `{user_id}`\n📧 জিমেইল: `{email}`\n🔑 পাসওয়ার্ড: `{password}`",
                reply_markup=InlineKeyboardMarkup(admin_keyboard),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to notify admin about Gmail submission: {e}")

        user_states.pop(user_id, None)
        user_temp_data.pop(user_id, None)
        await update.message.reply_text("প্রধান মেনু:", reply_markup=get_main_menu())

    elif state == "waiting_withdraw":
        await update.message.reply_text("✅ আপনার উইথড্র রিকোয়েস্ট সফলভাবে জমা হয়েছে! এডমিন পেমেন্ট কমপ্লিট করে দেবেন。")
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

# Background Auto Scheduler for Group Messages
async def daily_scheduler(application):
    while True:
        now = datetime.now()
        current_time = now.strftime("%H:%M")

        if current_time == "19:00":
            try:
                msg = (
                    "📢 **জরুরি ঘোষণা!**\n\n"
                    "এখন থেকে জিমেইল নেওয়া হচ্ছে。 যারা যারা জিমেইল দিতে চাচ্ছেন， তাড়াতাড়ি নিচের লিংকে প্রবেশ করে বটের মধ্যে জিমেইল সাবমিট করুন!\n\n"
                    f"👉 বট লিংক: {BOT_LINK}"
                )
                await application.bot.send_message(chat_id=GROUP_CHAT_ID, text=msg, parse_mode="Markdown")
            except Exception as e:
                logger.error(f"Failed to send 7 PM scheduled message: {e}")
            await asyncio.sleep(60)

        elif current_time == "22:30":
            try:
                msg = (
                    "🛑 **নোটিশ:**\n\n"
                    "আজকের মতো জিমেইল নেওয়া শেষ! এরপর থেকে আর জিমেইল নেওয়া হবে না。 অনুগ্রহ করে আগামীকাল থেকে জিমেইল দিবেন। ধন্যবাদ。\n\n"
                    "⚠️ একটু পর সবার জিমেইল চেক করা হবে। চেকের পরে যাদের যাদের পেমেন্ট রেডি হয়েছে， তারা পেমেন্টের জন্য বটের মাধ্যমে সাবমিট করুন। ধন্যবাদ。"
                )
                await application.bot.send_message(chat_id=GROUP_CHAT_ID, text=msg, parse_mode="Markdown")
            except Exception as e:
                logger.error(f"Failed to send 10:30 PM scheduled message: {e}")
            await asyncio.sleep(60)

        await asyncio.sleep(30)

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
    application.add_handler(CallbackQueryHandler(check_join_callback, pattern="^check_join$"))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(ChatJoinRequestHandler(handle_chat_join_request))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await run_web_server()
    logger.info("Starting Telegram Bot...")

    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    asyncio.create_task(daily_scheduler(application))

    stop_event = asyncio.Event()
    await stop_event.wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
