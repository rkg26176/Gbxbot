import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from flask import Flask
import threading

# Flask server banayein taaki Render ise dynamic web service maane
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running perfectly!"

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

WEB_APP_URL = "https://rkg26176.github.io/Gbxbot/"

CHANNELS = {
    "-1003332858806": {"name": "📢 GBX LOOT", "url": "https://t.me/+6ByfGDRBKgsxMjZl"},
    "-1003630519339": {"name": "📢 GBX EARN", "url": "https://t.me/+OWrCoeF-JutmNjg1"},
    "-1003197501531": {"name": "📢 GBX ZONE", "url": "https://t.me/+f2mWfDs6EUIxYTBl"}
}

def check_user_joined(user_id):
    for channel_id in CHANNELS:
        try:
            member = bot.get_chat_member(chat_id=int(channel_id), user_id=user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception as e:
            print(f"Error checking channel {channel_id}: {e}")
            return False
    return True

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    if check_user_joined(user_id):
        show_arena_button(message.chat.id, user_name, is_edit=False)
    else:
        show_force_join_buttons(message.chat.id, user_name, is_edit=False)

def show_force_join_buttons(chat_id, user_name, message_id=None, is_edit=False):
    text = f"❌ **Access Denied, {user_name}!**\n\nYou must join all our official channels first to unlock the IPL Swiggy Arena."
    
    markup = InlineKeyboardMarkup(row_width=1)
    for ch_id, ch_info in CHANNELS.items():
        btn = InlineKeyboardButton(text=ch_info["name"], url=ch_info["url"])
        markup.add(btn)
        
    verify_btn = InlineKeyboardButton(text="🔄 Check Joined / Verify", callback_data="verify_join")
    markup.add(verify_btn)

    if is_edit and message_id:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="Markdown")
    else:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

def show_arena_button(chat_id, user_name, message_id=None, is_edit=False):
    text = f"✅ **Verification Successful!**\n\nWelcome {user_name} to **IPL Swiggy Arena**. Click below to enter."
    
    markup = InlineKeyboardMarkup()
    web_app_info = WebAppInfo(url=WEB_APP_URL)
    arena_btn = InlineKeyboardButton(text="🎯 OPEN LOOT ARENA", web_app=web_app_info)
    markup.add(arena_btn)

    if is_edit and message_id:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="Markdown")
    else:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "verify_join")
def handle_verification(call):
    user_id = call.from_user.id
    user_name = call.from_user.first_name
    
    if check_user_joined(user_id):
        bot.answer_callback_query(call.id, "🎉 Success! Arena Unlocked.")
        show_arena_button(call.message.chat.id, user_name, call.message.message_id, is_edit=True)
    else:
        bot.answer_callback_query(call.id, "❌ Please join all 3 channels first!", show_alert=True)

# Bot ko background thread me chalane ke liye function
def run_bot():
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

if __name__ == '__main__':
    # Telegram bot ko alag thread me chalu karenge taaki Flask block na ho
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    # Render ka dynamic port uthane ke liye aur Flask ko active rakhne ke liye
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
    
