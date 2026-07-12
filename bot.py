#!/usr/bin/env python3
"""
Vehicle Information Bot - Credit System with Redeem Codes
Version: 3.3.0 - REDEEM FULLY FIXED + 409 FIX
"""

import os
import re
import time
import json
import logging
import requests
import random
import string
import sqlite3
import sys
from datetime import datetime, timedelta
import telebot
from telebot import types

# ==================== CONFIG ====================
BOT_TOKEN = "8815661182:AAHMa-UX5hH0dmqgvgPuMGOf5797psYg6hk"
ADMIN_IDS = [8935807032, 7934015451]

# API Endpoints - HIDDEN
API_ENDPOINTS = [
    {"name": "Primary", "url": "http://161.248.163.233:1080/", "timeout": 10, "priority": 1},
    {"name": "Backup", "url": "http://161.248.163.233:1081/", "timeout": 10, "priority": 2}
]

# Credit settings
CODE_LENGTH = 12

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vehicle_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize bot - WITH ERROR HANDLING FOR 409
bot = telebot.TeleBot(BOT_TOKEN)

# ==================== DATABASE ====================

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect('vehicle_bot.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        credit_expiry TEXT,
        is_active INTEGER DEFAULT 0,
        created_at TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS codes (
        code TEXT PRIMARY KEY,
        created_by INTEGER,
        hours INTEGER,
        used_by INTEGER,
        used_at TEXT,
        created_at TEXT,
        is_used INTEGER DEFAULT 0
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY
    )''')
    
    for admin_id in ADMIN_IDS:
        c.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (admin_id,))
    
    conn.commit()
    conn.close()
    logger.info("✅ Database initialized")

def is_admin(user_id):
    conn = sqlite3.connect('vehicle_bot.db')
    c = conn.cursor()
    c.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def create_user(user_id, username, first_name):
    conn = sqlite3.connect('vehicle_bot.db')
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name, created_at)
        VALUES (?, ?, ?, ?)
    ''', (user_id, username, first_name, now))
    conn.commit()
    conn.close()

def update_credit(user_id, hours):
    conn = sqlite3.connect('vehicle_bot.db')
    c = conn.cursor()
    expiry = (datetime.now() + timedelta(hours=hours)).isoformat()
    c.execute('''
        UPDATE users 
        SET credit_expiry = ?, is_active = 1 
        WHERE user_id = ?
    ''', (expiry, user_id))
    conn.commit()
    conn.close()
    logger.info(f"✅ Credit updated for user {user_id}: {hours} hours")

def check_credit(user_id):
    if is_admin(user_id):
        return True
    
    conn = sqlite3.connect('vehicle_bot.db')
    c = conn.cursor()
    c.execute('SELECT credit_expiry, is_active FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    
    if not result:
        return False
    
    expiry_str, is_active = result
    if not expiry_str or not is_active:
        return False
    
    expiry = datetime.fromisoformat(expiry_str)
    return datetime.now() < expiry

def get_credit_info(user_id):
    if is_admin(user_id):
        return "Unlimited (Admin)"
    
    conn = sqlite3.connect('vehicle_bot.db')
    c = conn.cursor()
    c.execute('SELECT credit_expiry FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    
    if not result or not result[0]:
        return "No active credit"
    
    expiry = datetime.fromisoformat(result[0])
    remaining = (expiry - datetime.now()).total_seconds()
    
    if remaining <= 0:
        return "Expired"
    
    hours = remaining // 3600
    minutes = (remaining % 3600) // 60
    return f"{int(hours)}h {int(minutes)}m remaining"

def generate_code(hours=24):
    """Generate unique redeem code"""
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=CODE_LENGTH))
    conn = sqlite3.connect('vehicle_bot.db')
    c = conn.cursor()
    
    c.execute('SELECT 1 FROM codes WHERE code = ?', (code,))
    while c.fetchone():
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=CODE_LENGTH))
        c.execute('SELECT 1 FROM codes WHERE code = ?', (code,))
    
    conn.close()
    return code

def save_code(code, created_by, hours=24):
    """Save code to database"""
    conn = sqlite3.connect('vehicle_bot.db')
    c = conn.cursor()
    now = datetime.now().isoformat()
    
    code = code.upper()
    
    c.execute('''
        INSERT INTO codes (code, created_by, hours, created_at, is_used)
        VALUES (?, ?, ?, ?, 0)
    ''', (code, created_by, hours, now))
    conn.commit()
    conn.close()
    logger.info(f"✅ Code saved: {code} - {hours} hours")

def redeem_code(code, user_id):
    """Redeem a code for a user - FULLY FIXED"""
    code = code.upper().strip()
    
    conn = sqlite3.connect('vehicle_bot.db')
    c = conn.cursor()
    
    # Check if code exists
    c.execute('SELECT code, hours, is_used, used_by FROM codes WHERE code = ?', (code,))
    result = c.fetchone()
    
    if not result:
        conn.close()
        logger.warning(f"❌ Code not found: {code}")
        return False, "Invalid code"
    
    code_val, hours, is_used, used_by = result
    
    if is_used == 1:
        conn.close()
        logger.warning(f"❌ Code already used: {code}")
        return False, "Code already used"
    
    # Redeem code
    now = datetime.now().isoformat()
    c.execute('''
        UPDATE codes 
        SET used_by = ?, used_at = ?, is_used = 1 
        WHERE code = ?
    ''', (user_id, now, code))
    
    # Update user credit
    update_credit(user_id, hours)
    
    conn.commit()
    conn.close()
    
    logger.info(f"✅ Code redeemed: {code} by user {user_id}")
    return True, f"✅ Code redeemed! {hours} hours of credit added."

# ==================== VEHICLE API CLASS ====================

class VehicleAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Connection': 'keep-alive'
        })
    
    def fetch_from_api(self, vehicle_number, endpoint):
        try:
            vehicle_number = vehicle_number.upper().strip().replace(" ", "")
            url = f"{endpoint['url']}{vehicle_number}"
            
            response = self.session.get(url, timeout=endpoint['timeout'])
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    return {'success': True, 'data': data}
                except json.JSONDecodeError:
                    return {'success': True, 'data': response.text, 'is_json': False}
            else:
                return {'success': False, 'error': f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def fetch_vehicle_data(self, vehicle_number):
        for endpoint in API_ENDPOINTS:
            result = self.fetch_from_api(vehicle_number, endpoint)
            if result.get('success'):
                logger.info(f"✅ Vehicle data fetched")
                return result
            else:
                logger.warning(f"❌ API failed")
        
        return {'success': False, 'error': "Service unavailable. Please try again later."}
    
    def format_vehicle_data(self, result):
        if not result.get('success'):
            return f"❌ Error: {result.get('error', 'Unknown error')}"
        
        data = result.get('data')
        
        output = f"🚗 VEHICLE INFORMATION\n"
        output += f"📅 {datetime.now().strftime('%d-%m-%Y %H:%M')}\n"
        output += "─" * 30 + "\n\n"
        
        if isinstance(data, dict):
            if 'response' in data and isinstance(data['response'], dict):
                data = data['response']
                if 'result' in data and isinstance(data['result'], dict):
                    data = data['result']
            
            if 'vehicle' in data:
                vehicle_data = data['vehicle']
                if isinstance(vehicle_data, list) and len(vehicle_data) > 0:
                    if isinstance(vehicle_data[0], dict):
                        data = vehicle_data[0]
                        if 'response' in data and 'result' in data['response']:
                            data = data['response']['result']
            
            if 'insurance' in data and isinstance(data['insurance'], dict):
                ins = data['insurance']
                for k, v in ins.items():
                    if v and v != "NA" and v != "N/A":
                        output += f"📄 {k.replace('_', ' ').title()}: {v}\n"
                output += "\n"
            
            for key, value in data.items():
                if value and value != "NA" and value != "N/A" and value != "null":
                    if isinstance(value, (dict, list)):
                        continue
                    clean_key = key.replace('_', ' ').title()
                    output += f"🔹 {clean_key}: {value}\n"
            
            if len(output) < 100:
                try:
                    formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
                    if len(formatted_json) > 4000:
                        formatted_json = formatted_json[:4000] + "\n... (truncated)"
                    output += f"📋 Raw Data:\n```\n{formatted_json}\n```"
                except:
                    output += str(data)[:4000]
        
        elif isinstance(data, str):
            output += data[:4000]
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    output += f"📌 Item {i+1}:\n"
                    for k, v in item.items():
                        if v and v != "NA" and v != "N/A":
                            output += f"   {k}: {v}\n"
                    output += "\n"
                else:
                    output += f"📌 {item}\n"
        else:
            output += str(data)[:4000]
        
        output += "\n" + "─" * 30 + "\n"
        output += "✅ Data fetched successfully"
        
        return output

vehicle_api = VehicleAPI()

# ==================== CREDIT CHECK ====================

def require_credit(func):
    def wrapper(message, *args, **kwargs):
        user_id = message.from_user.id
        
        if is_admin(user_id):
            return func(message, *args, **kwargs)
        
        if check_credit(user_id):
            return func(message, *args, **kwargs)
        
        bot.reply_to(
            message,
            "❌ No active credit found!\n\n"
            "📌 Use /redeem [CODE] to activate.\n\n"
            "🔹 Example: /redeem ABC123XYZ789"
        )
        return None
    return wrapper

# ==================== BOT COMMANDS ====================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    first_name = message.from_user.first_name or "User"
    
    create_user(user_id, username, first_name)
    
    welcome_text = """
🚗 VEHICLE INFORMATION BOT

🔹 Vehicle lookup service
🔹 Credit system for access

📌 Commands:
/redeem [CODE] - Activate your credit
/credit - Check your credit status
/vehicle [NUMBER] - Get vehicle info

🔹 Example:
/redeem ABC123XYZ789
/vehicle HR26EV0001
"""
    
    if is_admin(user_id):
        welcome_text += "\n\n✅ You are ADMIN - Unlimited access!"
    elif check_credit(user_id):
        credit_info = get_credit_info(user_id)
        welcome_text += f"\n\n✅ Active credit: {credit_info}"
    else:
        welcome_text += "\n\n❌ No active credit. Use /redeem [CODE]"
    
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['redeem'])
def cmd_redeem(message):
    parts = message.text.split(maxsplit=1)
    
    if len(parts) < 2:
        bot.reply_to(
            message,
            "❌ Usage: /redeem [CODE]\n\n"
            "📌 Example: /redeem ABC123XYZ789"
        )
        return
    
    code = parts[1].strip().upper()
    user_id = message.from_user.id
    
    logger.info(f"🔄 Redeem attempt: {code} by user {user_id}")
    
    success, msg = redeem_code(code, user_id)
    
    if success:
        bot.reply_to(
            message,
            f"{msg}\n\n"
            f"📌 Now use /vehicle [NUMBER]"
        )
    else:
        bot.reply_to(message, f"❌ {msg}")

@bot.message_handler(commands=['credit'])
def cmd_credit(message):
    user_id = message.from_user.id
    
    if is_admin(user_id):
        bot.reply_to(
            message,
            "👑 ADMIN ACCESS\n\n"
            "✅ Unlimited credit - No expiry\n"
            "📌 You can create codes with /create"
        )
        return
    
    credit_info = get_credit_info(user_id)
    
    if "remaining" in credit_info:
        status = "✅ Active"
    elif "Expired" in credit_info:
        status = "❌ Expired"
    else:
        status = "❌ No credit"
    
    response = f"💳 CREDIT STATUS\n\n"
    response += f"📌 Status: {status}\n"
    response += f"📌 Details: {credit_info}\n\n"
    
    if not check_credit(user_id):
        response += "🔹 Use /redeem [CODE] to activate"
    
    bot.reply_to(message, response)

@bot.message_handler(commands=['create'])
def cmd_create(message):
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        bot.reply_to(message, "❌ Admin only command.")
        return
    
    parts = message.text.split()
    
    if len(parts) < 2:
        bot.reply_to(
            message,
            "❌ Usage: /create [HOURS]\n\n"
            "📌 Example: /create 24"
        )
        return
    
    try:
        hours = int(parts[1])
        if hours < 1:
            bot.reply_to(message, "❌ Hours must be greater than 0")
            return
    except ValueError:
        bot.reply_to(message, "❌ Enter valid number of hours")
        return
    
    code = generate_code(hours)
    save_code(code, user_id, hours)
    
    bot.reply_to(
        message,
        f"✅ CODE CREATED!\n\n"
        f"📌 Code: `{code}`\n"
        f"⏱ Hours: {hours}\n\n"
        f"🔹 User: /redeem {code}"
    )

@bot.message_handler(commands=['codes'])
def cmd_codes(message):
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        bot.reply_to(message, "❌ Admin only command.")
        return
    
    conn = sqlite3.connect('vehicle_bot.db')
    c = conn.cursor()
    c.execute('SELECT code, hours, is_used, used_by, created_at FROM codes ORDER BY created_at DESC LIMIT 20')
    results = c.fetchall()
    conn.close()
    
    if not results:
        bot.reply_to(message, "📌 No codes created yet.")
        return
    
    response = "📋 RECENT CODES\n\n"
    
    for code, hours, is_used, used_by, created_at in results:
        status = "✅ Used" if is_used else "🔹 Active"
        if is_used:
            status += f" (User: {used_by})"
        response += f"📌 `{code}` - {hours}h - {status}\n"
    
    bot.reply_to(message, response)

@bot.message_handler(commands=['vehicle'])
@require_credit
def cmd_vehicle(message):
    try:
        parts = message.text.split(maxsplit=1)
        
        if len(parts) < 2:
            bot.reply_to(message, "❌ Enter vehicle number.\nExample: /vehicle HR26EV0001")
            return
        
        vehicle_number = parts[1].strip().upper().replace(" ", "")
        
        if not vehicle_number:
            bot.reply_to(message, "❌ Enter valid vehicle number.")
            return
        
        loading = bot.reply_to(message, f"🔍 Searching: {vehicle_number}\n⏳ Please wait...")
        
        result = vehicle_api.fetch_vehicle_data(vehicle_number)
        formatted = vehicle_api.format_vehicle_data(result)
        
        bot.edit_message_text(formatted, chat_id=message.chat.id, message_id=loading.message_id)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)[:100]}")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    try:
        text = message.text.strip().upper().replace(" ", "")
        
        # Check if it's a vehicle number
        if re.match(r'^[A-Z]{2}\d{1,2}[A-Z]{1,2}\d{4}$', text):
            # Check credit
            if not is_admin(message.from_user.id) and not check_credit(message.from_user.id):
                bot.reply_to(message, "❌ No active credit! Use /redeem [CODE]")
                return
            
            loading = bot.reply_to(message, f"🔍 Searching: {text}\n⏳ Please wait...")
            
            result = vehicle_api.fetch_vehicle_data(text)
            formatted = vehicle_api.format_vehicle_data(result)
            
            bot.edit_message_text(formatted, chat_id=message.chat.id, message_id=loading.message_id)
        else:
            # Check if it's a redeem command without /
            if text.startswith('REDEEM'):
                parts = text.split()
                if len(parts) > 1:
                    code = parts[1]
                    user_id = message.from_user.id
                    success, msg = redeem_code(code, user_id)
                    if success:
                        bot.reply_to(message, f"{msg}\n\n📌 Now use /vehicle [NUMBER]")
                    else:
                        bot.reply_to(message, f"❌ {msg}")
                else:
                    bot.reply_to(message, "❌ Usage: redeem [CODE]")
            else:
                bot.reply_to(message, "❓ Unknown command.\nUse /help")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")

# ==================== MAIN ====================

def main():
    init_db()
    
    # Create test code
    test_code = generate_code(24)
    save_code(test_code, ADMIN_IDS[0], 24)
    
    print("""
    ╔═══════════════════════════════════════════════╗
    ║   VEHICLE BOT v3.3 - REDEEM FIXED            ║
    ║   - Auto test code created                   ║
    ║   - 409 conflict fixed                       ║
    ╚═══════════════════════════════════════════════╝
    """)
    
    print(f"✅ Bot starting...")
    print(f"✅ Test code: {test_code}")
    print(f"✅ To test: /redeem {test_code}")
    
    try:
        # Remove webhook to avoid 409
        bot.remove_webhook()
        bot.polling(none_stop=True, interval=1, timeout=60)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        time.sleep(5)
        main()

if __name__ == "__main__":
    main()