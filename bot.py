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

# Naya GC add karke ab total 4 targets ho gaye hain
CHANNELS = {
    "-1003332858806": {"name": "📢 GBX LOOT", "url": "https://t.me/+6ByfGDRBKgsxMjZl"},
    "-1003630519339": {"name": "📢 GBX EARN", "url": "https://t.me/+OWrCoeF-JutmNjg1"},
    "-1003197501531": {"name": "📢 GBX ZONE", "url": "https://t.me/+f2mWfDs6EUIxYTBl"},
    "-1003862251237": {"name": "💬 Join Group Chat (GC)", "url": "https://t.me/+O_-kEF2f5f1kMjdl"}
}

# Background me check karega ki user ne kaun-kaun sa target join kiya hai
def get_user_status_map(user_id):
    status_map = {}
    for channel_id in CHANNELS:
        try:
            member = bot.get_chat_member(chat_id=int(channel_id), user_id=user_id)
            if member.status in ['left', 'kicked']:
                status_map[channel_id] = False  # Join nahi kiya
            else:
                status_map[channel_id] = True   # Already joined hai
        except Exception as e:
            print(f"Error checking channel {channel_id}: {e}")
            status_map[channel_id] = False
    return status_map

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    status_map = get_user_status_map(user_id)
    
    # Agar saare true hain (sab join kar rakha hai)
    if all(status_map.values()):
        show_arena_button(message.chat.id, user_name, is_edit=False)
    else:
        show_dynamic_force_join(message.chat.id, user_name, status_map, is_edit=False)

# DYNAMIC KEYBOARD GENERATOR: Jo join ho chuka hai, use remove kar dega
def show_dynamic_force_join(chat_id, user_name, status_map, message_id=None, is_edit=False):
    text = f"❌ **Access Denied, {user_name}!**\n\nYou must join our official channels and GC first to unlock the IPL Swiggy Arena."
    
    markup = InlineKeyboardMarkup(row_width=1)
    
    # Sirf wahi buttons add honge jo user ne join NAHI kiye hain (Status is False)
    for ch_id, ch_info in CHANNELS.items():
        if not status_map[ch_id]:  # Agar join nahi kiya hai tabhi dikhao
            btn = InlineKeyboardButton(text=ch_info["name"], url=ch_info["url"])
            markup.add(btn)
        
    verify_btn = InlineKeyboardButton(text="🔄 Check Joined / Verify", callback_data="verify_join")
    markup.add(verify_btn)

    if is_edit and message_id:
        try:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="Markdown")
        except Exception as e:
            # Agar user bina koi naya channel join kiye verify dabata hai toh inline keyboard change nahi hoga, handle error
            print(f"Keyboard update warning (No change): {e}")
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
    
    status_map = get_user_status_map(user_id)
    
    # Case 1: Agar user ne sab join kar liya
    if all(status_map.values()):
        bot.answer_callback_query(call.id, "🎉 Success! Arena Unlocked.")
        show_arena_button(call.message.chat.id, user_name, call.message.message_id, is_edit=True)
    else:
        # Case 2: Agar abhi bhi kuch baki hain, toh un bache huye channels ke sath menu edit ho jayega
        bot.answer_callback_query(call.id, "❌ Please join the remaining targets first!", show_alert=False)
        show_dynamic_force_join(call.message.chat.id, user_name, status_map, call.message.message_id, is_edit=True)


# --- MINI APP WIRE RECEIVER NODE ---
@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    raw_payload = message.web_app_data.data
    
    try:
        if "^" in raw_payload:
            segmented_nodes = raw_payload.split("^")
            extracted_tx_code = segmented_nodes[0].split(":")[1]
            extracted_final_bill = segmented_nodes[1].split(":")[1]
            extracted_location = segmented_nodes[2].split(":")[1] if len(segmented_nodes) > 2 else "Not Captured"
            
            compiled_receipt = "🎉 **Order Placed Successfully!**\n"
            compiled_receipt += "────────────────────────\n"
            compiled_receipt += f"🆔 **Order ID:** `{extracted_tx_code}`\n"
            compiled_receipt += f"💵 **Total Payment Due:** **{extracted_final_bill}**\n"
            compiled_receipt += f"📍 **Location / Coordinates:**\n`{extracted_location}`\n"
            compiled_receipt += "────────────────────────\n"
            compiled_receipt += "🚚 *Status: Dispatch pending account clearance.*"
            
            bot.send_message(message.chat.id, compiled_receipt, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, f"🎉 **Order Received!**\n\n📦 *Payload Summary:* `{raw_payload}`")
            
    except Exception as e:
        print(f"Error processing text data string: {e}")
        bot.send_message(message.chat.id, f"🎉 **Order Placed Successfully!**\n\n📦 *Raw Data:* {raw_payload}")


# Bot ko background thread me chalane ke liye function
def run_bot():
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
    
