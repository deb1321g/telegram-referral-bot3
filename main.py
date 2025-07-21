import json
import os
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

BOT_TOKEN = "8021137416:AAESwqHNGmhx_dy3hrDJjyPmMG4SQmrU9LE"
WEBHOOK_URL = "https://telegram-referral-bot-r8ny.onrender.com"

CHANNELS = [
    {"name": "Channel 1", "username": "@movie_watch_with_robin"},
    {"name": "Channel 2", "username": "@movie_watch_with_robin1"},
    {"name": "Channel 3", "username": "@Bot_Domain_foryou"},
]

DATA_FILE = "users.json"

app = Flask(__name__)

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        users = json.load(f)
else:
    users = {}

def save_users():
    with open(DATA_FILE, "w") as f:
        json.dump(users, f)

async def is_member(user_id, context):
    for channel in CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel["username"], user_id=user_id)
            if member.status in ['left', 'kicked']:
                return False
        except:
            return False
    return True

async def send_force_join_message(update_or_callback, context):
    buttons = [
        [InlineKeyboardButton(f"🔗 Join {ch['name']}", url=f"https://t.me/{ch['username'].strip('@')}")]
        for ch in CHANNELS
    ]
    buttons.append([InlineKeyboardButton("✅ I have joined", callback_data="check_join")])
    reply_markup = InlineKeyboardMarkup(buttons)

    if isinstance(update_or_callback, Update) and update_or_callback.message:
        await update_or_callback.message.reply_text(
            "🔒 You must join the following channels to use the bot:",
            reply_markup=reply_markup
        )
    else:
        await update_or_callback.callback_query.edit_message_text(
            "🔒 You must join the following channels to use the bot:",
            reply_markup=reply_markup
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in users:
        users[user_id] = {"balance": 0, "bonus": False, "referred_by": None}
        if context.args:
            referrer = context.args[0]
            if referrer != user_id and referrer in users:
                users[user_id]["referred_by"] = referrer
                users[referrer]["balance"] += 1
        save_users()

    if not await is_member(user_id, context):
        await send_force_join_message(update, context)
        return

    keyboard = [["💰 Balance", "👫 Refer"],
                ["🎁 Bonus", "💸 Withdraw"],
                ["⚙️ Settings", "🆘 Support"]]
    await update.message.reply_text(
        "👋 Welcome to the Referral Bot!\nEarn balance by inviting friends.",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)

    if await is_member(user_id, context):
        keyboard = [["💰 Balance", "👫 Refer"],
                    ["🎁 Bonus", "💸 Withdraw"],
                    ["⚙️ Settings", "🆘 Support"]]
        await query.edit_message_text(
            "✅ You're verified!\n👋 Welcome to the Referral Bot!",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
    else:
        await send_force_join_message(update, context)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text

    if user_id not in users:
        await update.message.reply_text("❌ Please /start first.")
        return

    if not await is_member(user_id, context):
        await send_force_join_message(update, context)
        return

    if text == "💰 Balance":
        referrals = sum(1 for u in users.values() if u.get("referred_by") == user_id)
        await update.message.reply_text(
            f"💵 Your balance: ${users[user_id]['balance']}\n"
            f"👥 Total referrals: {referrals}\n\n"
            "🚨 Note: You must refer at least 20 people to enable the withdraw request system."
        )

    elif text == "👫 Refer":
        refer_link = f"https://t.me/{context.bot.username}?start={user_id}"
        referrals = sum(1 for u in users.values() if u.get("referred_by") == user_id)
        await update.message.reply_text(
            f"🔗 Your referral link:\n{refer_link}\n"
            f"👥 You have referred: {referrals} user(s)\n\n"
            "⚠️ Note: You need to refer 20 users to activate the withdraw system."
        )

    elif text == "🎁 Bonus":
        if not users[user_id]["bonus"]:
            users[user_id]["balance"] += 0.5
            users[user_id]["bonus"] = True
            save_users()
            await update.message.reply_text("🎁 Bonus claimed! You got $0.5.")
        else:
            await update.message.reply_text("✅ You already claimed your bonus.")

    elif text == "💸 Withdraw":
        await update.message.reply_text(
            "🚫 Withdraw is currently unavailable.\n\n"
            "📣 Refer 20 users to activate the withdraw request system."
        )

    elif text == "⚙️ Settings":
        await update.message.reply_text("⚙️ Settings is under development.")

    elif text == "🆘 Support":
        await update.message.reply_text("📩 Contact us at @YourSupportUsername")

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), bot.app.bot)
    await bot.app.update_queue.put(update)
    return "OK"

@app.route("/")
def root():
    return "Bot is Alive!"

async def main():
    global bot
    bot = Application.builder().token(BOT_TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CallbackQueryHandler(check_join_callback, pattern="check_join"))
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    await bot.bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")
    bot.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
    )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
