iimport logging
import os
import asyncio
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Admin ID & Support
ADMIN_ID = 7458685213
ADMIN_SUPPORT = "@nahidbro204"
OFFICIAL_GROUP_LINK = "https://t.me/nahidgmailsallar204"

# Final Category-wise Sell Prices
SELL_PRICES = {
    "1": 20.0,  # Fresh Gmail
    "2": 35.0,  # Old Gmail
    "3": 25.0,  # Recovery Added
    "4": 30.0,  # 2FA Enabled
    "5": 15.0   # Facebook Created Gmail
}

CATEGORY_NAMES = {
    "1": "Fresh Gmail",
    "2": "Old Gmail",
    "3": "Recovery Added",
    "4": "2FA Enabled",
    "5": "Facebook created Gmail"
}

# In-memory database
users_db = {}
order_counter = 1000

def get_user(user_id, referrer_id=None):
    if user_id not in users_db:
        users_db[user_id] = {
            'balance': 0.0,
            'referred_by': referrer_id,
            'team': [],
            'pending_action': None,
            'withdraw_data': {},
            'deposit_data': {},
            'sell_data': {},
            'is_verified': False
        }
        if referrer_id and referrer_id in users_db and referrer_id != user_id:
            if user_id not in users_db[referrer_id]['team']:
                users_db[referrer_id]['team'].append(user_id)
    return users_db[user_id]

# Start Command - Shows Notice and Join/Verify buttons first
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    referrer_id = int(args[0]) if args and args[0].isdigit() else None
    
    user_data = get_user(user.id, referrer_id)
    
    if user_data.get('is_verified'):
        await show_main_menu(update, context)
        return
    
    notice_text = (
        f"📢 **অফিসিয়াল নোটিশ!**\n\n"
        f"আসসালামু আলাইকুম {user.first_name}! আমাদের সকল নতুন আপডেট এবং সাপোর্ট পেতে প্রথমে আমাদের অফিসিয়াল গ্রুপে জয়েন করুন।\n\n"
        f"নিচের বাটনে চাপ দিয়ে গ্রুপে জয়েন করার পর **'Verify'** বাটনে চাপ দিন।"
    )
    
    keyboard = [
        [InlineKeyboardButton("📢 অফিসিয়াল গ্রুপে জয়েন করুন", url=OFFICIAL_GROUP_LINK)],
        [InlineKeyboardButton("✅ Verify (যাচাই করুন)", callback_data="verify_join")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(notice_text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(notice_text, reply_markup=reply_markup, parse_mode="Markdown")

# Function to display Main Menu
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("🛒 জিমেইল ক্রয় (Gmail Buy)", callback_data="menu_buy")],
        [InlineKeyboardButton("📤 জিমেইল বিক্রি (Gmail Sell)", callback_data="menu_sell")],
        [InlineKeyboardButton("💰 ডিপোজিট (Deposit)", callback_data="menu_deposit")],
        [InlineKeyboardButton("💸 উইথড্র (Withdraw)", callback_data="menu_withdraw")],
        [InlineKeyboardButton("👥 আমার টিম (My Team)", callback_data="menu_team")],
        [InlineKeyboardButton("👤 ব্যালেন্স ও প্রোফাইল", callback_data="menu_profile"),
         InlineKeyboardButton("📞 সাপোর্ট", url=f"https://t.me/{ADMIN_SUPPORT.replace('@','')}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        f"🌟 **স্বাগতম, {user.first_name}!**\n\n"
        f"আমাদের ডিজিটাল সার্ভিস শপে আপনাকে স্বাগতম। নিচে থেকে আপনার প্রয়োজনীয় অপশনটি সিলেক্ট করুন:"
    )
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

# Main Menu Callback Handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_data = get_user(user_id)
    
    data = query.data
    
    if data == "verify_join":
        user_data['pending_action'] = 'waiting_verify'
        await query.message.edit_text(
            "⏳ আপনার ভেরিফিকেশন রিকোয়েস্টটি অ্যাডমিনের কাছে পাঠানো হয়েছে। অনুগ্রহ করে অনুমোদনের অপেক্ষা করুন...",
            parse_mode="Markdown"
        )
        
        admin_text = (
            f"🔔 **নতুন মেম্বার ভেরিফিকেশন রিকোয়েস্ট!**\n\n"
            f"👤 User ID: `{user_id}`\n"
            f"👤 Username: @{query.from_user.username if query.from_user.username else 'N/A'}\n"
            f"📌 Status: 🟡 Pending"
        )
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"admin_approve_verify_{user_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"admin_cancel_verify_{user_id}")
            ]
        ]
        await context.bot.send_message(ADMIN_ID, admin_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    elif data.startswith("admin_approve_verify_"):
        target_user_id = int(data.split("_")[3])
        target_user = get_user(target_user_id)
        target_user['is_verified'] = True
        
        await query.message.edit_text(query.message.text.replace("Status: 🟡 Pending", "Status: ✅ Approved") + f"\n\n✅ **অ্যাডমিন কর্তৃক ভেরিফাইড**")
        try:
            keyboard = [
                [InlineKeyboardButton("🛒 জিমেইল ক্রয় (Gmail Buy)", callback_data="menu_buy")],
                [InlineKeyboardButton("📤 জিমেইল বিক্রি (Gmail Sell)", callback_data="menu_sell")],
                [InlineKeyboardButton("💰 ডিপোজিট (Deposit)", callback_data="menu_deposit")],
                [InlineKeyboardButton("💸 উইথড্র (Withdraw)", callback_data="menu_withdraw")],
                [InlineKeyboardButton("👥 আমার টিম (My Team)", callback_data="menu_team")],
                [InlineKeyboardButton("👤 ব্যালেন্স ও প্রোফাইল", callback_data="menu_profile"),
                 InlineKeyboardButton("📞 সাপোর্ট", url=f"https://t.me/{ADMIN_SUPPORT.replace('@','')}")]
            ]
            await context.bot.send_message(
                target_user_id, 
                "✅ **আপনার ভেরিফিকেশন সফল হয়েছে!**\n\nআমাদের বট ব্যবহার করার জন্য আপনাকে স্বাগতম। নিচে থেকে অপশন সিলেক্ট করুন:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        except:
            pass
        return

    elif data.startswith("admin_cancel_verify_"):
        target_user_id = int(data.split("_")[3])
        await query.message.edit_text(query.message.text.replace("Status: 🟡 Pending", "Status: ❌ Cancelled") + f"\n\n❌ **ভেরিফিকেশন বাতিল করা হয়েছে**")
        try:
            await context.bot.send_message(target_user_id, "❌ আপনার ভেরিফিকেশন রিকোয়েস্টটি বাতিল করা হয়েছে। অনুগ্রহ করে নিয়ম মেনে গ্রুপে জয়েন করে আবার চেষ্টা করুন।")
        except:
            pass
        return

    elif data.startswith("admin_approve_buy_"):
        parts = data.split("_")
        target_user_id = int(parts[3])
        quantity = int(parts[4])
        total_cost = float(parts[5])
        
        target_user = get_user(target_user_id)
        if target_user['balance'] >= total_cost:
            target_user['balance'] -= total_cost
            await query.message.edit_text(query.message.text.replace("Status: 🟡 Pending", "Status: ✅ Approved") + f"\n\n✅ **অর্ডার সফলভাবে অনুমোদিত হয়েছে!**")
            try:
                await context.bot.send_message(
                    target_user_id, 
                    f"✅ আপনার জিমেইল ক্রয়ের অর্ডারটি অ্যাডমিন কর্তৃক অনুমোদিত হয়েছে!\n"
                    f"📦 পরিমাণ: {quantity}টি জিমেইল\n\n"
                    f"জিমেইলগুলো সংগ্রহ করতে বা কথা বলতে সরাসরি অ্যাডমিদের সাথে যোগাযোগ করুন:\n👉 {ADMIN_SUPPORT}"
                )
            except:
                pass
        else:
            await query.message.edit_text(query.message.text + "\n\n❌ ইউজারের পর্যাপ্ত ব্যালেন্স নেই।")
        return

    elif data.startswith("admin_cancel_buy_"):
        target_user_id = int(data.split("_")[3])
        quantity = int(data.split("_")[4])
        total_cost = float(data.split("_")[5])
        
        target_user = get_user(target_user_id)
        # Refund balance if cancelled
        target_user['balance'] += total_cost
        
        await query.message.edit_text(query.message.text.replace("Status: 🟡 Pending", "Status: ❌ Cancelled") + f"\n\n❌ **অর্ডার বাতিল করা হয়েছে ও ব্যালেন্স ফেরত দেওয়া হয়েছে**")
        try:
            await context.bot.send_message(target_user_id, f"❌ আপনার জিমেইল ক্রয়ের রিকোয়েস্টটি ({quantity} পিস) বাতিল করা হয়েছে এবং আপনার {total_cost} BDT ব্যালেন্সে ফিরিয়ে দেওয়া হয়েছে।")
        except:
            pass
        return

    if data == "main_menu":
        user_data['pending_action'] = None
        user_data['sell_data'] = {}
        await show_main_menu(update, context)
        
    elif data == "menu_buy":
        user_data['pending_action'] = 'buy_gmail'
        text = (
            "🛒 **জিমেইল ক্রয় মেনু** 🛒\n\n"
            "🟢 **স্ট্যাটাস:** `স্টক এভেইলেবল`\n"
            "💵 **মূল্য:** `প্রতি পিস জিমেইল মাত্র ৩০ টাকা (30 BDT)`\n\n"
            "📝 **আপনি কতগুলো জিমেইল ক্রয় করবেন নিচে সংখ্যায় লিখে পাঠান:**"
        )
        keyboard = [[InlineKeyboardButton("🔙 মূল মেনু", callback_data="main_menu")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        
    elif data == "menu_sell":
        user_data['pending_action'] = 'sell_get_gmail'
        user_data['sell_data'] = {}
        text = (
            "📤 **জিমেইল বিক্রি মেনু**\n\n"
            "আপনার পছন্দের ক্যাটাগরিটি সিলেক্ট করুন:"
        )
        cats = [
            ("1", "1. Fresh Gmail (২০ টাকা)"), 
            ("2", "2. Old Gmail (৩৫ টাকা)"), 
            ("3", "3. Recovery Added (২৫ টাকা)"), 
            ("4", "4. 2FA Enabled (৩০ টাকা)"),
            ("5", "5. Facebook created Gmail (১৫ টাকা)")
        ]
        keyboard = [[InlineKeyboardButton(label, callback_data=f"sell_cat_{cat_id}")] for cat_id, label in cats]
        keyboard.append([InlineKeyboardButton("🔙 মূল মেনু", callback_data="main_menu")])
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        
    elif data.startswith("sell_cat_"):
        cat_id = data.split("_")[2]
        user_data['sell_data']['cat_id'] = cat_id
        user_data['pending_action'] = 'sell_get_gmail'
        
        cat_name = CATEGORY_NAMES.get(cat_id, "Unknown")
        price = SELL_PRICES.get(cat_id, 20.0)
        
        text = (
            f"📤 **ক্যাটাগরি:** `{cat_name}` (রেট: `{price} BDT`)\n\n"
            "✉️ **প্রথমে আপনার জিমেইল (Gmail) টি লিখে পাঠান:**"
        )
        keyboard = [[InlineKeyboardButton("🔙 ফিরে যান", callback_data="menu_sell")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "menu_deposit":
        user_data['pending_action'] = 'deposit_amount'
        text = (
            "💰 **ডিপোজিট মেনু**\n\n"
            "নিচের নম্বরে সেন্ড মানি করুন:\n"
            "📌 **বিকাশ / নগদ (পার্সোনাল):** `01715914270`\n\n"
            "⚠️ **সর্বনিম্ন ডিপোজিট ৬০ টাকা।**\n\n"
            "📝 **আপনি কত টাকা ডিপোজিট করেছেন তা অঙ্কে লিখে পাঠান (যেমন: 100):**"
        )
        keyboard = [[InlineKeyboardButton("🔙 মূল মেনু", callback_data="main_menu")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "menu_withdraw":
        user_data['pending_action'] = 'withdraw_method'
        text = (
            "💸 **উইথড্র মেনু**\n\n"
            "আপনার অ্যাকাউন্ট ব্যালেন্স: **" + str(user_data['balance']) + " BDT**\n\n"
            "দয়া করে পেমেন্ট মেথড সিলেক্ট করুন:"
        )
        keyboard = [
            [InlineKeyboardButton("bKash (Personal)", callback_data="wd_bkash")],
            [InlineKeyboardButton("Nagad (Personal)", callback_data="wd_nagad")],
            [InlineKeyboardButton("🔙 মূল মেনু", callback_data="main_menu")]
        ]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data in ["wd_bkash", "wd_nagad"]:
        method = "bKash (Personal)" if data == "wd_bkash" else "Nagad (Personal)"
        user_data['withdraw_data']['method'] = method
        user_data['pending_action'] = 'withdraw_amount'
        
        text = (
            f"💸 **উইথড্র - {method}**\n\n"
            "📝 **আপনি কত টাকা উইথড্র করতে চান তা লিখুন:**\n"
            "⚠️ _সর্বনিম্ন উইথড্র ৬০ টাকা।_"
        )
        keyboard = [[InlineKeyboardButton("🔙 ফিরে যান", callback_data="menu_withdraw")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "menu_team":
        team_list = user_data['team']
        total_team = len(team_list)
        bot_info = await context.bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        
        text = (
            f"👥 **আপনার টিম ও রেফারেল রিপোর্ট**\n\n"
            f"🔹 **মোট টিম মেম্বার:** `{total_team} জন`\n\n"
            f"🔗 **আপনার রেফারেল লিংক:**\n`{ref_link}`\n\n"
            f"📋 **আপনার টিমের তালিকা:**\n"
        )
        if total_team == 0:
            text += "এখনো কেউ আপনার লিংকে জয়েন করেনি।"
        else:
            for idx, member_id in enumerate(team_list, 1):
                text += f"{idx}. User ID: `{member_id}`\n"
                
        keyboard = [[InlineKeyboardButton("🔙 মূল মেনু", callback_data="main_menu")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "menu_profile":
        text = (
            f"👤 **আপনার প্রোফাইল**\n\n"
            f"🆔 **ইউজার আইডি:** `{user_id}`\n"
            f"💰 **ব্যালেন্স:** `{user_data['balance']} BDT`\n"
            f"👥 **মোট রেফারেল:** `{len(user_data['team'])}`"
        )
        keyboard = [[InlineKeyboardButton("🔙 মূল মেনু", callback_data="main_menu")]]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("admin_approve_dep_"):
        target_user_id = int(data.split("_")[3])
        amount = float(data.split("_")[4])
        target_user = get_user(target_user_id)
        target_user['balance'] += amount
        
        await query.message.edit_text(query.message.text.replace("Status: 🟡 Pending", "Status: ✅ Approved") + f"\n\n✅ **অ্যাডমিন কর্তৃক অনুমোদিত (ডিপোজিট: {amount} BDT)**")
        try:
            await context.bot.send_message(target_user_id, f"✅ আপনার ডিপোজিট সফল হয়েছে! আপনার অ্যাকাউন্টে {amount} BDT যোগ করা হয়েছে।")
        except:
            pass

    elif data.startswith("admin_cancel_dep_"):
        target_user_id = int(data.split("_")[3])
        amount = float(data.split("_")[4])
        
        await query.message.edit_text(query.message.text.replace("Status: 🟡 Pending", "Status: ❌ Cancelled") + f"\n\n❌ **অ্যাডমিন কর্তৃক বাতিল (ডিপোজিট: {amount} BDT)**")
        try:
            await context.bot.send_message(target_user_id, f"❌ আপনার ডিপোজিট রিকোয়েস্টটি ({amount} BDT) বাতিল করা হয়েছে।")
        except:
            pass

    elif data.startswith("admin_approve_sell_"):
        parts = data.split("_")
        target_user_id = int(parts[3])
        cat_id = parts[4]
        sell_reward = SELL_PRICES.get(cat_id, 20.0)
        
        target_user = get_user(target_user_id)
        target_user['balance'] += sell_reward
        
        await query.message.edit_text(query.message.text.replace("Status: 🟡 Pending", "Status: ✅ Approved") + f"\n\n✅ **জিমেইল বিক্রি অনুমোদিত (ব্যালেন্সে {sell_reward} BDT যোগ করা হয়েছে)**")
        try:
            await context.bot.send_message(target_user_id, f"✅ আপনার জিমেইল বিক্রি সফল হয়েছে! অ্যাডমিন যাচাই করে আপনার অ্যাকাউন্টে {sell_reward} BDT যোগ করেছেন।")
        except:
            pass

    elif data.startswith("admin_cancel_sell_"):
        target_user_id = int(data.split("_")[3])
        await query.message.edit_text(query.message.text.replace("Status: 🟡 Pending", "Status: ❌ Cancelled") + f"\n\n❌ **জিমেইলের অর্ডার বাতিল করা হয়েছে**")
        try:
            await context.bot.send_message(target_user_id, f"❌ আপনার জিমেইল বিক্রির রিকোয়েস্টটি বাতিল করা হয়েছে।")
        except:
            pass

    elif data.startswith("admin_approve_wd_"):
        target_user_id = int(data.split("_")[3])
        amount = float(data.split("_")[4])
        
        await query.message.edit_text(query.message.text + f"\n\n✅ **সফলভাবে পেমেন্ট করা হয়েছে (অ্যাডমিন)**")
        try:
            await context.bot.send_message(target_user_id, f"✅ আপনার উইথড্র সফল হয়েছে! অ্যাডমিন পেমেন্ট সম্পন্ন করেছেন ({amount} BDT)।")
        except:
            pass

    elif data.startswith("admin_reject_wd_"):
        target_user_id = int(data.split("_")[3])
        amount = float(data.split("_")[4])
        target_user = get_user(target_user_id)
        target_user['balance'] += amount  
        
        await query.message.edit_text(query.message.text + f"\n\n❌ **বাতিল করা হয়েছে (ব্যালেন্স ফেরত দেওয়া হয়েছে)**")
        try:
            await context.bot.send_message(target_user_id, f"❌ আপনার উইথড্র রিকোয়েস্টটি বাতিল করা হয়েছে এবং {amount} BDT আপনার অ্যাকাউন্টে ফিরিয়ে দেওয়া হয়েছে।")
        except:
            pass

# Message / Input Handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global order_counter
    user = update.effective_user
    user_id = user.id
    user_data = get_user(user_id)
    text = update.message.text.strip()
    
    action = user_data.get('pending_action')
    if not action:
        return

    if action == 'buy_gmail':
        if not text.isdigit():
            await update.message.reply_text("❌ দয়া করে সঠিক সংখ্যা লিখুন।")
            return
        
        quantity = int(text)
        total_cost = quantity * 30
        
        if user_data['balance'] < total_cost:
            await update.message.reply_text("❌ আপনার অ্যাকাউন্টে পর্যাপ্ত ব্যালেন্স নেই।")
            return
        
        user_data['balance'] -= total_cost
        user_data['pending_action'] = None
        
        await update.message.reply_text(
            f"✅ আপনার অর্ডারটি সফলভাবে গ্রহণ করা হয়েছে!\n"
            f"🛒 পরিমাণ: {quantity}টি জিমেইল\n"
            f"💵 মোট খরচ: {total_cost} BDT\n"
            f"⏳ স্ট্যাটাস: **Pending (অ্যাডমিন শীঘ্রই ডেলিভারি দেবেন)**"
        )
        
        admin_text = (
            f"🔔 **নতুন জিমেইল ক্রয়ের অর্ডার!**\n\n"
            f"👤 User ID: `{user_id}`\n"
            f"👤 Username: @{user.username if user.username else 'N/A'}\n"
            f"📦 Quantity: {quantity} Pcs\n"
            f"💵 Total Cost: {total_cost} BDT\n"
            f"📌 Status: 🟡 Pending"
        )
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"admin_approve_buy_{user_id}_{quantity}_{total_cost}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"admin_cancel_buy_{user_id}_{quantity}_{total_cost}")
            ]
        ]
        await context.bot.send_message(ADMIN_ID, admin_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif action == 'sell_get_gmail':
        if 'cat_id' not in user_data['sell_data']:
            user_data['sell_data']['cat_id'] = "1"
            
        user_data['sell_data']['gmail'] = text
        user_data['pending_action'] = 'sell_get_password'
        
        await update.message.reply_text("🔑 **দয়া করে পাসওয়ার্ড (Password) লিখে পাঠান:**")

    elif action == 'sell_get_password':
        user_data['sell_data']['password'] = text
        
        cat_id = user_data['sell_data'].get('cat_id', '1')
        gmail = user_data['sell_data'].get('gmail', '')
        password = user_data['sell_data'].get('password', '')
        
        user_data['pending_action'] = None
        user_data['sell_data'] = {}
        
        order_counter += 1
        current_order_id = order_counter
        
        cat_name = CATEGORY_NAMES.get(cat_id, "Unknown")
        reward = SELL_PRICES.get(cat_id, 20.0)
        
        await update.message.reply_text(
            f"⏳ **আপনার জিমেইলের বিবরণ সফলভাবে গ্রহণ করা হয়েছে!**\n"
            f"📋 অর্ডার নম্বর: `#{current_order_id}`\n"
            f"🔄 স্ট্যাটাস: `যাচাই করা হচ্ছে (Pending)`\n\n"
            f"অ্যাডমিন যাচাই করে আপনার ব্যালেন্স আপডেট করে দেবেন।"
        )
        
        admin_text = (
            f"🔔 **নতুন জিমেইল বিক্রির রিকোয়েস্ট!**\n\n"
            f"📋 **Order Number:** `#{current_order_id}`\n"
            f"👤 **User ID:** `{user_id}`\n"
            f"👤 **Username:** @{user.username if user.username else 'N/A'}\n"
            f"🏷️ **Category:** {cat_name} (ID: {cat_id})\n"
            f"💵 **Reward:** {reward} BDT\n\n"
            f"📧 **Gmail:**\n`{gmail}`\n\n"
            f"🔑 **Password:**\n`{password}`\n\n"
            f"📌 **Status:** 🟡 Pending"
        )
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"admin_approve_sell_{user_id}_{cat_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"admin_cancel_sell_{user_id}")
            ]
        ]
        await context.bot.send_message(ADMIN_ID, admin_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif action == 'deposit_amount':
        if not text.replace('.', '', 1).isdigit():
            await update.message.reply_text("❌ দয়া করে সঠিক টাকার পরিমাণ লিখুন।")
            return
        
        amount = float(text)
        if amount < 60:
            await update.message.reply_text("❌ সর্বনিম্ন ডিপোজিট ৬০ টাকা।")
            return
            
        user_data['deposit_data']['amount'] = amount
        user_data['pending_action'] = 'deposit_trxid'
        
        await update.message.reply_text("📝 **এখন আপনার বিকাশ/নগদ ট্রানজেকশন আইডি (TrxID) বা বিবরণ লিখে পাঠান:**")

    elif action == 'deposit_trxid':
        trx_info = text
        amount = user_data['deposit_data'].get('amount', 0)
        user_data['pending_action'] = None
        user_data['deposit_data'] = {}
        
        await update.message.reply_text("✅ আপনার ডিপোজিট রিকোয়েস্ট এবং TrxID অ্যাডমিনের কাছে পাঠানো হয়েছে। অনুগ্রহ করে অনুমোদনের অপেক্ষা করুন।")
        
        admin_text = (
            f"🔔 **নতুন ডিপোজিট রিকোয়েস্ট!**\n\n"
            f"👤 User ID: `{user_id}`\n"
            f"💰 Amount: {amount} BDT\n"
            f"📝 TrxID / Info: `{trx_info}`\n"
            f"📌 Status: 🟡 Pending"
        )
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"admin_approve_dep_{user_id}_{amount}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"admin_cancel_dep_{user_id}_{amount}")
            ]
        ]
        await context.bot.send_message(ADMIN_ID, admin_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif action == 'withdraw_amount':
        if not text.replace('.', '', 1).isdigit():
            await update.message.reply_text("❌ দয়া করে সঠিক টাকার পরিমাণ লিখুন।")
            return
            
        amount = float(text)
        if amount < 60:
            await update.message.reply_text("❌ আপনার অ্যাকাউন্টে পর্যাপ্ত টাকা নাই (সর্বনিম্ন ৬০ টাকা)।")
            return
            
        if user_data['balance'] < amount:
            await update.message.reply_text("❌ আপনার অ্যাকাউন্টে পর্যাপ্ত ব্যালেন্স নেই।")
            return
            
        user_data['withdraw_data']['amount'] = amount
        user_data['pending_action'] = 'withdraw_number'
        
        await update.message.reply_text(
            "📞 **রিসিভার অ্যাকাউন্ট নম্বর দিন:**\n\n"
            "⚠️ _সতর্কবার্তা: অবশ্যই সঠিক নম্বর ইনপুট করুন। ভুল নম্বরে পেমেন্ট চলে গেলে কর্তৃপক্ষ দায়ী থাকবে না।_"
        )

    elif action == 'withdraw_number':
        number = text
        wd_data = user_data['withdraw_data']
        method = wd_data.get('method')
        amount = wd_data.get('amount')
        
        user_data['balance'] -= amount
        user_data['pending_action'] = None
        user_data['withdraw_data'] = {}
        
        await update.message.reply_text("⏳ আপনার উইথড্র রিকোয়েস্টটি পেন্ডিং আছে। অ্যাডমিন পেমেন্ট করার পর সফল (Successful) দেখানো হবে।")
        
        admin_text = (
            f"🔔 **নতুন উইথড্র রিকোয়েস্ট!**\n\n"
            f"👤 User ID: `{user_id}`\n"
            f"💳 Method: {method}\n"
            f"💰 Amount: {amount} BDT\n"
            f"📱 Receiver Number: `{number}`"
        )
        keyboard = [
            [
                InlineKeyboardButton("✅ Success", callback_data=f"admin_approve_wd_{user_id}_{amount}"),
                InlineKeyboardButton("❌ Cancel (Refund)", callback_data=f"admin_reject_wd_{user_id}_{amount}")
            ]
        ]
        await context.bot.send_message(ADMIN_ID, admin_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# Web server handler for Render health check
async def handle_web(request):
    return web.Response(text="Bot is active and running 24/7!")

async def main():
    TOKEN = "9197059198:AAF-uRkXSJjGiQF54qsBXKBBfK53H9l5s3Q"
    
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    # Initialize and start bot application properly in async loop
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    app = web.Application()
    app.router.add_get("/", handle_web)
    
    port = int(os.environ.get("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    print(f"Web server started on port {port} and bot polling active 24/7...")

    # Keep alive indefinitely
    stop_signal = asyncio.Event()
    await stop_signal.wait()

if __name__ == '__main__':
    asyncio.run(main())
