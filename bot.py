#!/usr/bin/env python3
"""
Vehicle Information Bot - Dual API Failover System
Version: 2.2.0 - QUOTE FORMAT
"""

import os
import re
import time
import json
import logging
import requests
from datetime import datetime
import telebot
from telebot import types

# ==================== CONFIG ====================
BOT_TOKEN = "8815661182:AAHMa-UX5hH0dmqgvgPuMGOf5797psYg6hk"
ADMIN_IDS = [8935807032, 7934015451]

# API Endpoints - Primary and Backup
API_ENDPOINTS = [
    {
        "name": "Primary",
        "url": "http://161.248.163.233:1080/",
        "timeout": 10,
        "priority": 1
    },
    {
        "name": "Backup",
        "url": "http://161.248.163.233:1081/",
        "timeout": 10,
        "priority": 2
    }
]

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

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# User sessions
user_sessions = {}

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
        """Fetch data from a specific API endpoint"""
        try:
            vehicle_number = vehicle_number.upper().strip().replace(" ", "")
            url = f"{endpoint['url']}{vehicle_number}"
            
            logger.info(f"Trying {endpoint['name']} API: {url}")
            
            response = self.session.get(url, timeout=endpoint['timeout'])
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    return {
                        'success': True,
                        'data': data,
                        'api': endpoint['name'],
                        'url': url
                    }
                except json.JSONDecodeError:
                    return {
                        'success': True,
                        'data': response.text,
                        'api': endpoint['name'],
                        'url': url,
                        'is_json': False
                    }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}",
                    'api': endpoint['name']
                }
                
        except requests.exceptions.Timeout:
            return {'success': False, 'error': "Timeout", 'api': endpoint['name']}
        except requests.exceptions.ConnectionError:
            return {'success': False, 'error': "Connection Error", 'api': endpoint['name']}
        except Exception as e:
            return {'success': False, 'error': str(e), 'api': endpoint['name']}
    
    def fetch_vehicle_data(self, vehicle_number):
        """Fetch vehicle data with failover"""
        for endpoint in API_ENDPOINTS:
            result = self.fetch_from_api(vehicle_number, endpoint)
            if result.get('success'):
                logger.info(f"✅ {endpoint['name']} API returned data")
                return result
            else:
                logger.warning(f"❌ {endpoint['name']} API failed: {result.get('error')}")
        
        return {
            'success': False,
            'error': "All APIs failed. Please try again later."
        }
    
    def format_vehicle_data(self, result):
        """Format vehicle data in clean QUOTE format"""
        if not result.get('success'):
            return f"❌ Error: {result.get('error', 'Unknown error')}"
        
        data = result.get('data')
        api_name = result.get('api', 'Unknown')
        
        # Start with header
        output = f"🚗 VEHICLE INFORMATION\n"
        output += f"📡 Source: {api_name} API\n"
        output += f"📅 {datetime.now().strftime('%d-%m-%Y %H:%M')}\n"
        output += "─" * 30 + "\n\n"
        
        # If data is dict, format nicely
        if isinstance(data, dict):
            # Clean and display key fields first
            important_keys = [
                'regn_no', 'regn_dt', 'vehicle_cd', 'vh_class_desc',
                'chasi_no', 'eng_no', 'color', 'manu_yr',
                'fla_maker_desc', 'fla_model_desc', 'fla_variant',
                'fla_fuel_type_desc', 'fla_cubic_cap', 'fla_seat_cap',
                'owner_sr', 'rto_name', 'state_cd', 'fit_upto',
                'tax_upto', 'permit_issue_dt', 'permit_valid_from',
                'insurance_comp', 'insurance_policy_no', 'insurance_upto'
            ]
            
            # Check for nested data
            if 'response' in data and isinstance(data['response'], dict):
                data = data['response']
                if 'result' in data and isinstance(data['result'], dict):
                    data = data['result']
            
            # Try to get vehicle details
            if 'vehicle' in data:
                vehicle_data = data['vehicle']
                if isinstance(vehicle_data, list) and len(vehicle_data) > 0:
                    # Get first vehicle
                    if isinstance(vehicle_data[0], dict):
                        data = vehicle_data[0]
                        # Check for deeper nesting
                        if 'response' in data and 'result' in data['response']:
                            data = data['response']['result']
            
            # Handle insurance data
            if 'insurance' in data and isinstance(data['insurance'], dict):
                ins = data['insurance']
                for k, v in ins.items():
                    if v and v != "NA" and v != "N/A":
                        output += f"📄 {k.replace('_', ' ').title()}: {v}\n"
                output += "\n"
            
            # Display all fields in clean format
            for key, value in data.items():
                if value and value != "NA" and value != "N/A" and value != "null":
                    # Skip nested objects, handle them above
                    if isinstance(value, (dict, list)):
                        continue
                    # Clean key name
                    clean_key = key.replace('_', ' ').title()
                    # Format value
                    output += f"🔹 {clean_key}: {value}\n"
            
            # If no fields found, show raw JSON
            if len(output) < 100:
                try:
                    formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
                    if len(formatted_json) > 4000:
                        formatted_json = formatted_json[:4000] + "\n... (truncated)"
                    output += f"📋 Raw Data:\n```\n{formatted_json}\n```"
                except:
                    output += str(data)[:4000]
        
        # If data is string
        elif isinstance(data, str):
            output += data[:4000]
        
        # If data is list
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
        
        # Add footer
        output += "\n" + "─" * 30 + "\n"
        output += "✅ Data fetched successfully"
        
        return output

# Initialize API
vehicle_api = VehicleAPI()

# ==================== BOT COMMANDS ====================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """
🚗 VEHICLE INFORMATION BOT

🔹 Dual API Failover System
🔹 Primary + Backup APIs
🔹 Auto-switch if one fails

📌 Commands:
/vehicle HR26EV0001 - Get vehicle info
/status - Check API status
/apis - List all APIs
/help - Show help

📌 Example:
/vehicle HR26EV0001
"""
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
📚 HELP

📌 /vehicle HR26EV0001 - Get vehicle info
📌 /status - Check API status
📌 /apis - List all APIs

📌 Supported Formats:
HR26EV0001
Up14BC4321
PB65AM0008
Any Indian vehicle number

📌 Data Provided:
- Registration details
- Insurance info
- Vehicle specs
- Ownership details
"""
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['status'])
def cmd_status(message):
    status_msg = "🔍 API STATUS CHECK\n"
    status_msg += "─" * 30 + "\n\n"
    
    for endpoint in API_ENDPOINTS:
        status_msg += f"📡 {endpoint['name']} API\n"
        status_msg += f"🔗 {endpoint['url']}\n"
        
        try:
            test_vehicle = "HR26EV0001"
            response = requests.get(f"{endpoint['url']}{test_vehicle}", timeout=5)
            
            if response.status_code == 200:
                status_msg += "✅ Status: Online\n"
                status_msg += f"📊 Response: {len(response.text)} bytes\n"
            else:
                status_msg += f"⚠️ Status: Error (HTTP {response.status_code})\n"
        except Exception as e:
            status_msg += f"❌ Status: Offline\n"
        
        status_msg += "\n"
    
    status_msg += "─" * 30 + "\n"
    status_msg += f"📅 {datetime.now().strftime('%d-%m-%Y %H:%M')}"
    
    bot.reply_to(message, status_msg)

@bot.message_handler(commands=['apis'])
def cmd_apis(message):
    apis_text = "📡 CONFIGURED APIS\n"
    apis_text += "─" * 30 + "\n\n"
    
    for endpoint in API_ENDPOINTS:
        apis_text += f"📌 {endpoint['name']} API\n"
        apis_text += f"🔗 {endpoint['url']}\n"
        apis_text += f"⏱ Timeout: {endpoint['timeout']}s\n"
        apis_text += f"⚡ Priority: {endpoint['priority']}\n\n"
    
    apis_text += "─" * 30 + "\n"
    apis_text += "🔄 Failover Logic:\n"
    apis_text += "1️⃣ Try Primary API\n"
    apis_text += "2️⃣ If fails, try Backup API\n"
    apis_text += "3️⃣ If both fail, show error"
    
    bot.reply_to(message, apis_text)

@bot.message_handler(commands=['vehicle'])
def cmd_vehicle(message):
    try:
        command_parts = message.text.split(maxsplit=1)
        
        if len(command_parts) < 2:
            bot.reply_to(
                message,
                "❌ Enter vehicle number.\n\n"
                "📌 Example: /vehicle HR26EV0001"
            )
            return
        
        vehicle_number = command_parts[1].strip().upper().replace(" ", "")
        
        if not vehicle_number:
            bot.reply_to(message, "❌ Enter valid vehicle number.")
            return
        
        loading_msg = bot.reply_to(
            message,
            f"🔍 Searching for: {vehicle_number}\n"
            f"⏳ Trying Primary API...\n"
            f"📅 {datetime.now().strftime('%d-%m-%Y %H:%M')}"
        )
        
        result = vehicle_api.fetch_vehicle_data(vehicle_number)
        formatted_data = vehicle_api.format_vehicle_data(result)
        
        bot.edit_message_text(
            formatted_data,
            chat_id=message.chat.id,
            message_id=loading_msg.message_id
        )
        
        if result.get('success'):
            logger.info(f"✅ Vehicle: {vehicle_number} - API: {result.get('api')}")
        else:
            logger.warning(f"❌ Vehicle: {vehicle_number} - Failed")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)[:100]}")
        logger.error(f"Error: {str(e)}")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    try:
        text = message.text.strip().upper().replace(" ", "")
        
        vehicle_pattern = r'^[A-Z]{2}\d{1,2}[A-Z]{1,2}\d{4}$'
        
        if re.match(vehicle_pattern, text):
            loading_msg = bot.reply_to(
                message,
                f"🔍 Searching for: {text}\n"
                f"⏳ Trying Primary API...\n"
                f"📅 {datetime.now().strftime('%d-%m-%Y %H:%M')}"
            )
            
            result = vehicle_api.fetch_vehicle_data(text)
            formatted_data = vehicle_api.format_vehicle_data(result)
            
            bot.edit_message_text(
                formatted_data,
                chat_id=message.chat.id,
                message_id=loading_msg.message_id
            )
            
            if result.get('success'):
                logger.info(f"✅ Vehicle: {text} - API: {result.get('api')}")
            else:
                logger.warning(f"❌ Vehicle: {text} - Failed")
        else:
            bot.reply_to(
                message,
                "❓ Unknown command.\n\n"
                "📌 Use /help to see commands."
            )
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")

# ==================== ADMIN ====================

@bot.message_handler(commands=['admin'])
def cmd_admin(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "❌ Not authorized.")
        return
    
    admin_text = """
👑 ADMIN PANEL

📌 /status - Check APIs
📌 /apis - List APIs

📌 Bot Status: ✅ Running
📌 API Failover: ✅ Active
📌 Primary: 161.248.163.233:1080
📌 Backup: 161.248.163.233:1081
"""
    bot.reply_to(message, admin_text)

@bot.message_handler(func=lambda message: True)
def default_handler(message):
    bot.reply_to(
        message,
        "❓ Unknown command.\n\n"
        "📌 Use /help to see commands."
    )

# ==================== MAIN ====================

def main():
    print("""
    ╔═══════════════════════════════════════════════╗
    ║   VEHICLE BOT v2.2 - QUOTE FORMAT            ║
    ╚═══════════════════════════════════════════════╝
    """)
    
    print(f"✅ Bot starting...")
    print(f"✅ APIs: {len(API_ENDPOINTS)}")
    
    try:
        bot.polling(none_stop=True, interval=1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        time.sleep(5)
        main()

if __name__ == "__main__":
    main()