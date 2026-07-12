#!/usr/bin/env python3
import os
import re
import time
import json
import logging
import requests
import random
import string
import sqlite3
from datetime import datetime, timedelta
import telebot

# ==================== CONFIG ====================
BOT_TOKEN = "8815661182:AAHMa-UX5hH0dmqgvgPuMGOf5797psYg6hk"
ADMIN_IDS = [8935807032, 7934015451]

API_URLS = [
    "http://161.248.163.233:1080/",
    "http://161.248.163.233:1081/"
]

CODE_LENGTH = 12

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== DATABASE ====================

def get_db():
    conn = sqlite3.connect('vehicle_bot.db', timeout=20)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        credit_expiry TEXT,
        is_active INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS codes (
        code TEXT PRIMARY KEY,
        hours INTEGER,
        used_by INTEGER,
        used_at TEXT,
        created_at TEXT,
        expiry_time TEXT,
        is_used INTEGER DEFAULT 0
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY
    )''')
    for aid in ADMIN_IDS:
        c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (aid,))
    conn.commit()
    conn.close()
    logger.info("✅ DB ready")

def is_admin(uid):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT 1 FROM admins WHERE user_id = ?', (uid,))
    r = c.fetchone()
    conn.close()
    return r is not None

def has_credit(uid):
    if is_admin(uid):
        return True
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT credit_expiry FROM users WHERE user_id = ?', (uid,))
    r = c.fetchone()
    conn.close()
    if not r or not r[0]:
        return False
    try:
        return datetime.now() < datetime.fromisoformat(r[0])
    except:
        return False

def get_credit_info(uid):
    if is_admin(uid):
        return "Unlimited Admin"
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT credit_expiry FROM users WHERE user_id = ?', (uid,))
    r = c.fetchone()
    conn.close()
    if not r or not r[0]:
        return "No credit"
    try:
        rem = (datetime.fromisoformat(r[0]) - datetime.now()).total_seconds()
        if rem <= 0:
            return "Expired"
        return f"{int(rem//3600)}h {int((rem%3600)//60)}m"
    except:
        return "Invalid"

def add_credit(uid, hours):
    conn = get_db()
    c = conn.cursor()
    expiry = (datetime.now() + timedelta(hours=hours)).isoformat()
    c.execute('INSERT OR REPLACE INTO users (user_id, credit_expiry, is_active) VALUES (?, ?, 1)', (uid, expiry))
    conn.commit()
    conn.close()

def create_user(uid):
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (uid,))
    conn.commit()
    conn.close()

def gen_code(hours=24):
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=CODE_LENGTH))
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT 1 FROM codes WHERE code = ?', (code,))
    while c.fetchone():
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=CODE_LENGTH))
        c.execute('SELECT 1 FROM codes WHERE code = ?', (code,))
    conn.close()
    return code

def save_code(code, hours):
    conn = get_db()
    c = conn.cursor()
    now = datetime.now().isoformat()
    expiry = (datetime.now() + timedelta(hours=hours)).isoformat()
    c.execute('INSERT INTO codes (code, hours, created_at, expiry_time, is_used) VALUES (?, ?, ?, ?, 0)',
              (code, hours, now, expiry))
    conn.commit()
    conn.close()

def redeem_code(code, uid):
    code = code.upper().strip()
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT hours, is_used, expiry_time FROM codes WHERE code = ?', (code,))
    r = c.fetchone()
    if not r:
        conn.close()
        return False, "❌ Invalid code"
    hours, is_used, expiry = r
    if is_used:
        conn.close()
        return False, "❌ Code already used"
    if datetime.now() > datetime.fromisoformat(expiry):
        conn.close()
        return False, "❌ Code expired"
    c.execute('UPDATE codes SET used_by = ?, used_at = ?, is_used = 1 WHERE code = ?', (uid, datetime.now().isoformat(), code))
    add_credit(uid, hours)
    create_user(uid)
    conn.commit()
    conn.close()
    return True, f"✅ Code redeemed! {hours} hours added!"

def get_all_codes(limit=30):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM codes ORDER BY created_at DESC LIMIT ?', (limit,))
    r = c.fetchall()
    conn.close()
    return r

def get_user_codes(uid):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM codes WHERE used_by = ? ORDER BY used_at DESC', (uid,))
    r = c.fetchall()
    conn.close()
    return r

# ==================== API ====================

def fetch_vehicle(number):
    number = number.upper().strip().replace(" ", "")
    for url in API_URLS:
        try:
            resp = requests.get(f"{url}{number}", timeout=10)
            if resp.status_code == 200:
                try:
                    return {'success': True, 'data': resp.json()}
                except:
                    return {'success': True, 'data': resp.text}
        except:
            continue
    return {'success': False, 'error': "API down"}

def format_vehicle(data):
    if not data.get('success'):
        return f"❌ {data.get('error', 'Unknown error')}"
    
    d = data.get('data')
    output = f"🚗 VEHICLE INFO\n📅 {datetime.now().strftime('%d-%m-%Y %H:%M')}\n{'─'*30}\n\n"
    
    if isinstance(d, dict):
        if 'response' in d:
            d = d['response']
        if 'result' in d:
            d = d['result']
        if 'vehicle' in d and isinstance(d['vehicle'], list) and len(d['vehicle']) > 0:
            d = d['vehicle'][0]
            if 'response' in d and 'result' in d['response']:
                d = d['response']['result']
        
        for k, v in d.items():
            if v and v not in ['NA', 'N/A', 'null', '']:
                if not isinstance(v, (dict, list)):
                    output += f"🔹 {k.replace('_', ' ').title()}: {v}\n"
        
        if len(output) < 100:
            output += json.dumps(d, indent=2, ensure_ascii=False)[:4000]
    
    elif isinstance(d, str):
        output += d[:4000]
    else:
        output += str(d)[:4000]
    
    output += f"\n\n{'─'*30}\n✅ Done"
    return output

# ==================== BOT ====================

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(m):
    uid = m.from_user.id
    create_user(uid)
    
    text = "🚗 VEHICLE BOT\n\n"
    text += "/redeem [CODE] - Activate\n"
    text += "/credit - Check status\n"
    text += "/vehicle [NUMBER] - Search\n"
    text += "/mycodes - Your codes\n"
    
    if is_admin(uid):
        text += "\n👑 ADMIN:\n/create [HOURS]\n/codes"
        text += f"\n\n✅ Unlimited access"
    elif has_credit(uid):
        text += f"\n\n✅ {get_credit_info(uid)}"
    else:
        text += "\n\n❌ No credit. Use /redeem"
    
    bot.reply_to(m, text)

@bot.message_handler(commands=['redeem'])
def redeem(m):
    parts = m.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(m, "❌ /redeem [CODE]")
        return
    ok, msg = redeem_code(parts[1].strip(), m.from_user.id)
    bot.reply_to(m, msg)

@bot.message_handler(commands=['credit'])
def credit(m):
    uid = m.from_user.id
    if is_admin(uid):
        bot.reply_to(m, "👑 Admin - Unlimited")
        return
    bot.reply_to(m, f"💳 {get_credit_info(uid)}")

@bot.message_handler(commands=['vehicle'])
def vehicle(m):
    uid = m.from_user.id
    if not is_admin(uid) and not has_credit(uid):
        bot.reply_to(m, "❌ No credit! Use /redeem")
        return
    
    parts = m.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(m, "❌ /vehicle HR26EV0001")
        return
    
    num = parts[1].strip().upper().replace(" ", "")
    if not num:
        bot.reply_to(m, "❌ Invalid number")
        return
    
    loading = bot.reply_to(m, f"🔍 Searching {num}...")
    result = fetch_vehicle(num)
    formatted = format_vehicle(result)
    bot.edit_message_text(formatted, chat_id=m.chat.id, message_id=loading.message_id)

@bot.message_handler(commands=['create'])
def create(m):
    if not is_admin(m.from_user.id):
        bot.reply_to(m, "❌ Admin only")
        return
    
    parts = m.text.split()
    if len(parts) < 2:
        bot.reply_to(m, "❌ /create 24")
        return
    
    try:
        hours = int(parts[1])
        if hours < 1:
            bot.reply_to(m, "❌ > 0")
            return
    except:
        bot.reply_to(m, "❌ Invalid number")
        return
    
    code = gen_code(hours)
    save_code(code, hours)
    bot.reply_to(m, f"✅ Code: `{code}`\n{hours}h\n/redeem {code}")

@bot.message_handler(commands=['codes'])
def codes(m):
    if not is_admin(m.from_user.id):
        bot.reply_to(m, "❌ Admin only")
        return
    
    rows = get_all_codes(30)
    if not rows:
        bot.reply_to(m, "No codes")
        return
    
    text = "📋 CODES\n\n"
    for r in rows:
        code, hours, used_by, used_at, created_at, expiry, is_used = r
        status = "Used" if is_used else "Active"
        if is_used:
            status += f" (by {used_by})"
        text += f"`{code}` - {hours}h - {status}\n"
        text += f"  Expires: {expiry[:10]}\n\n"
    
    bot.reply_to(m, text)

@bot.message_handler(commands=['mycodes'])
def mycodes(m):
    rows = get_user_codes(m.from_user.id)
    if not rows:
        bot.reply_to(m, "No codes redeemed")
        return
    
    text = "📋 YOUR CODES\n\n"
    for r in rows:
        code, hours, used_by, used_at, created_at, expiry, is_used = r
        text += f"`{code}` - {hours}h\n"
        text += f"  Expires: {expiry[:10]}\n\n"
    
    bot.reply_to(m, text)

@bot.message_handler(func=lambda m: True)
def handle(m):
    text = m.text.strip().upper().replace(" ", "")
    if re.match(r'^[A-Z]{2}\d{1,2}[A-Z]{1,2}\d{4}$', text):
        uid = m.from_user.id
        if not is_admin(uid) and not has_credit(uid):
            bot.reply_to(m, "❌ No credit! Use /redeem")
            return
        
        loading = bot.reply_to(m, f"🔍 Searching {text}...")
        result = fetch_vehicle(text)
        formatted = format_vehicle(result)
        bot.edit_message_text(formatted, chat_id=m.chat.id, message_id=loading.message_id)
    else:
        bot.reply_to(m, "❓ Use /start")

# ==================== MAIN ====================

if __name__ == "__main__":
    init_db()
    
    # Create test code
    test_code = gen_code(24)
    save_code(test_code, 24)
    
    print("""
    ╔═══════════════════════════════════════════════╗
    ║   VEHICLE BOT - FINAL WORKING                ║
    ╚═══════════════════════════════════════════════╝
    """)
    print(f"✅ Test code: {test_code}")
    print(f"✅ /redeem {test_code}")
    print("✅ Bot running...")
    
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"❌ {e}")
        time.sleep(5)