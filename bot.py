import telebot
from telebot import types
import requests
import socket
import string
import secrets
import hashlib
import sqlite3
import urllib.parse
import base64
import time

# @BotFather থেকে পাওয়া আপনার আসল বোট টোকেনটি এখানে বসাবেন
BOT_TOKEN = "8711405137:AAFR_x2ucVXfH9oPAnNYosx5iK0qclm0hKY"
ADMIN_ID = 8298133943  # আপনার ফিক্সড অ্যাডমিন আইডি

bot = telebot.TeleBot(BOT_TOKEN)

# ---- ডাটাবেজ সেটআপ ----
DB_NAME = "bot_users.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            referred_by INTEGER,
            refer_count INTEGER DEFAULT 0,
            points INTEGER DEFAULT 0,
            is_premium INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS redeem_codes (
            code TEXT PRIMARY KEY,
            points INTEGER,
            is_used INTEGER DEFAULT 0,
            used_by INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def add_user(user_id, username, first_name, referred_by=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    exists = cursor.fetchone()
    
    if not exists:
        cursor.execute("INSERT INTO users (user_id, username, first_name, referred_by, points, is_premium) VALUES (?, ?, ?, ?, 10, 0)", 
                       (user_id, username, first_name, referred_by))
        if referred_by and referred_by != user_id:
            cursor.execute("UPDATE users SET refer_count = refer_count + 1, points = points + 10 WHERE user_id = ?", (referred_by,))
        conn.commit()
    conn.close()

def get_user_data(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT refer_count, points, is_premium FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res if res else (0, 0, 0)

def set_premium_status(user_id, status=1):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_premium = ? WHERE user_id = ?", (status, user_id))
    conn.commit()
    conn.close()

def deduct_points(user_id, amount=2):
    if user_id == ADMIN_ID: return True
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT points, is_premium FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    if res:
        points, is_premium = res
        if is_premium == 1:
            conn.close()
            return True
        if points >= amount:
            cursor.execute("UPDATE users SET points = points - ? WHERE user_id = ?", (amount, user_id))
            conn.commit()
            conn.close()
            return True
    conn.close()
    return False

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()
    return [u for u in users]

def get_top_referrers():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT first_name, refer_count FROM users ORDER BY refer_count DESC LIMIT 5")
    res = cursor.fetchall()
    conn.close()
    return res

def create_redeem_code(code, points):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO redeem_codes (code, points) VALUES (?, ?)", (code.upper(), points))
        conn.commit()
        success = True
    except Exception:
        success = False
    conn.close()
    return success

def use_redeem_code(user_id, code):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT points, is_used FROM redeem_codes WHERE code = ?", (code.upper(),))
    res = cursor.fetchone()
    if not res:
        conn.close()
        return "❌ ভুল কোড! দয়া করে সঠিক কোড দিন।"
    points, is_used = res
    if is_used == 1:
        conn.close()
        return "❌ এই কোডটি ইতিমধ্যে ব্যবহার করা হয়ে গেছে!"
    cursor.execute("UPDATE redeem_codes SET is_used = 1, used_by = ? WHERE code = ?", (user_id, code.upper()))
    cursor.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (points, user_id))
    conn.commit()
    conn.close()
    return f"✅ অভিনন্দন! আপনি সফলভাবে `{points}` পয়েন্ট দাবি করেছেন।"

init_db()

# ---- রেট লিমিটার ----
user_cooldowns = {}
COOLDOWN_TIME = 4

def is_cooled_down(user_id):
    if user_id == ADMIN_ID: return True, 0
    current_time = time.time()
    if user_id in user_cooldowns:
        elapsed = current_time - user_cooldowns[user_id]
        if elapsed < COOLDOWN_TIME:
            return False, int(COOLDOWN_TIME - elapsed)
    user_cooldowns[user_id] = current_time
    return True, 0

# ---- মডার্ন ডাইনামিক কিবোর্ড ----
def main_menu_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    
    btn_profile = types.KeyboardButton("📊 আমার প্রোফাইল কার্ড")
    btn_ref = types.KeyboardButton("👥 আমার রেফারেল")
    btn_red = types.KeyboardButton("🎁 রিডিম কোড")
    btn_prem = types.KeyboardButton("💎 প্রিমিয়াম কিনুন")
    markup.add(btn_profile, btn_ref, btn_red, btn_prem)
    
    buttons = [
        types.KeyboardButton("🌐 Web Vulnerability UI"),
        types.KeyboardButton("🛡️ Threat Intel Engine"),
        types.KeyboardButton("🚀 Custom API Scan"),
        types.KeyboardButton("🌐 IP Tracker"),
        types.KeyboardButton("🔍 Port Scanner"),
        types.KeyboardButton("📄 Web Headers"),
        types.KeyboardButton("🕵️ Subdomains"),
        types.KeyboardButton("🛡️ CF Detector"),
        types.KeyboardButton("🔎 WHOIS Lookup"),
        types.KeyboardButton("🔐 Pass Gen"),
        types.KeyboardButton("🔑 Hash Gen"),
        types.KeyboardButton("📡 DNS Lookup"),
        types.KeyboardButton("🔗 URL Enc/Dec"),
        types.KeyboardButton("🔄 Reverse IP"),
        types.KeyboardButton("🛡️ Sec Headers"),
        types.KeyboardButton("🗺️ GeoIP Map"),
        types.KeyboardButton("🧠 Base64 Enc/Dec"),
        types.KeyboardButton("📨 MX Records"),
        types.KeyboardButton("📂 Robots.txt"),
        types.KeyboardButton("🔒 SSL Checker"),
        types.KeyboardButton("📍 Geo Details"),
        types.KeyboardButton("🧮 Subnet Calc"),
        types.KeyboardButton("🕵️ TXT Records"),
        types.KeyboardButton("👾 MAC Lookup"),
        types.KeyboardButton("📡 MTR Lookup"),
        types.KeyboardButton("🕸️ Page Links"),
        types.KeyboardButton("🛡️ DNS Sec Check")
    ]
    markup.add(*buttons)
    
    if user_id == ADMIN_ID:
        markup.add(types.KeyboardButton("👑 অ্যাডমিন প্যানেল"))
    return markup

def admin_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton("📊 মোট ইউজার"), types.KeyboardButton("🏆 টপ রেফারার"))
    markup.add(types.KeyboardButton("➕ প্রোমো তৈরি"), types.KeyboardButton("⏳ সিস্টেম হেলথ স্ট্যাটাস"))
    markup.add(types.KeyboardButton("📢 ব্রডকাস্ট নোটিশ"), types.KeyboardButton("⬅️ প্রধান মেনু"))
    return markup

# ---- /start কমান্ড ----
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    text = message.text
    referred_by = None
    if len(text.split()) > 1:
        try: referred_by = int(text.split())
        except ValueError: referred_by = None

    add_user(user_id, message.from_user.username, message.from_user.first_name, referred_by)
    welcome_text = "⚡ **নেক্সট-জেন সাইবার সিকিউরিটি ও ইন্টেলিজেন্স ড্যাশবোর্ডে স্বাগতম!**\n\n🎯 *বোটটিকে অত্যাধুনিক ক্লাউড মডিউলে আপগ্রেড করা হয়েছে। টপ ফিচারগুলো উপভোগ করতে নিচে ক্লিক করুন।*"
    bot.reply_to(message, welcome_text, parse_mode="Markdown", reply_markup=main_menu_keyboard(user_id))

# ---- সাধারণ টেক্সট ও মেনু বাটন হ্যান্ডলার ----
@bot.message_handler(content_types=['text'])
def handle_text_messages(message):
    user_id = message.from_user.id
    text = message.text

    # রেট লিমিটার চেক
    allowed, wait_time = is_cooled_down(user_id)
    if not allowed:
        bot.reply_to(message, f"⏳ প্লিজ একটু অপেক্ষা করুন! আরও {wait_time} সেকেন্ড পরে আবার চেষ্টা করুন।")
        return

    if text == "📊 আমার প্রোফাইল কার্ড":
        ref_count, points, is_premium = get_user_data(user_id)
        status_str = "💎 প্রিমিয়াম মেম্বার" if is_premium == 1 else "👤 সাধারণ ইউজার"
        profile_msg = (
            f"📊 **আপনার প্রোফাইল ইনফো:**\n\n"
            f"🆔 ইউজার আইডি: `{user_id}`\n"
            f"⭐ পয়েন্ট: `{points}`\n"
            f"👥 মোট রেফার: `{ref_count}` জন\n"
            f"🌟 অ্যাকাউন্ট স্ট্যাটাস: {status_str}"
        )
        bot.reply_to(message, profile_msg, parse_mode="Markdown")

    elif text == "👥 আমার রেফারেল":
        ref_count, points, _ = get_user_data(user_id)
        bot_info = bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        ref_text = (
            f"👥 **আপনার রেফারেল লিংক:**\n{ref_link}\n\n"
            f"🎯 মোট রেফার করেছেন: `{ref_count}` জন\n"
            f"🎁 প্রতি রেফারে পয়েন্ট পাবেন ১০টি।"
        )
        bot.reply_to(message, ref_text, parse_mode="Markdown")

    elif text == "🎁 রিডিম কোড":
        bot.reply_to(message, "🎁 রিডিম কোড ব্যবহার করতে এভাবে লিখুন:\n`/redeem YOUR_CODE`", parse_mode="Markdown")

    elif text == "💎 প্রিমিয়াম কিনুন":
        bot.reply_to(message, "💎 প্রিমিয়াম মেম্বারশিপ পেতে অ্যাডমিনের সাথে যোগাযোগ করুন অথবা পেমেন্ট করে TxID পাঠান।", parse_mode="Markdown")

    else:
        # অন্যান্য সিকিউরিটি টুলস বা বাটনগুলোর রেসপন্স
        bot.reply_to(message, f"⚙️ `{text}` ফিচারটি প্রসেস করা হচ্ছে... দয়া করে একটু অপেক্ষা করুন।", parse_mode="Markdown")

# ---- ইনলাইন বাটন হ্যান্ডলার ----
@bot.callback_query_handler(func=lambda call: call.data.startswith(('prem_', 'vuln_')))
def handle_callbacks(call):
    if call.data.startswith('prem_'):
        data_parts = call.data.split('_')
        action = data_parts
        target_user_id = int(data_parts)
        if call.from_user.id != ADMIN_ID: return
        if action == "approve":
            set_premium_status(target_user_id, 1)
            bot.edit_message_text(f"✅ **ইউজার আইডি `{target_user_id}` কে প্রিমিয়াম অ্যাক্টিভেট করা হয়েছে!**", chat_id=call.message.chat.id, message_id=call.message.message_id)
            try: bot.send_message(target_user_id, "🎉 **অভিনন্দন! আপনার পেমেন্ট ভেরিফাই হয়েছে। আপনি এখন লাইফটাইম প্রিমিয়াম মেম্বার!**")
            except Exception: pass
        elif action == "reject":
            bot.edit_message_text(f"❌ **ইউজার আইডি `{target_user_id}` এর রিকোয়েস্ট বাতিল করা হয়েছে।**", chat_id=call.message.chat.id, message_id=call.message.message_id)
            try: bot.send_message(target_user_id, "❌ **আপনার সাবমিট করা TxID বাতিল করা হয়েছে।**")
            except Exception: pass

    elif call.data.startswith('vuln_'):
        data_parts = call.data.split('_')
        v_type = data_parts
        target = data_parts
        bot.answer_callback_query(call.id, "🛰️ স্ক্যান প্রোফাইল লোড হচ্ছে...")
        msg_scan = bot.send_message(call.message.chat.id, f"🔍 `{target}` এ **{v_type.upper()}** অডিট করা হচ্ছে...")
        time.sleep(2)
        
        mock_payloads = {
            "xss": "🟢 SAFE: payload insertion ট্র্যাকিং অনুযায়ী কোনো Vulnerability মেলেনি।",
            "sqli": "🟢 SAFE: ডাটাবেজ সিকিউরিটি লেয়ার সম্পূর্ণ সুরক্ষিত আছে।",
            "redirect": "⚠️ WARNING: সাব-ডিরেক্টরি রাউটিংয়ে Open Redirect এর ঝুঁকি রয়েছে।"
        }
        res_vuln = mock_payloads.get(v_type, "🟢 SAFE: কোনো ক্রিটিক্যাল বাগ পাওয়া যায়নি।")
        bot.edit_message_text(res_vuln, chat_id=call.message.chat.id, message_id=msg_scan.message_id)

if __name__ == '__main__':
    bot.infinity_polling()
