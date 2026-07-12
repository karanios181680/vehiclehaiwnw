#!/usr/bin/env python3
"""
Vehicle Information Bot - Dual API Failover System
Version: 2.1.0 - FIXED JSON PARSING
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
        """Format vehicle data for display - FIXED"""
        if not result.get('success'):
            return f"❌ Error: {result.get('error', 'Unknown error')}"
        
        data = result.get('data')
        api_name = result.get('api', 'Unknown')
        
        # Start with API info
        output = f"🚗 Vehicle Information\n"
        output += f"📡 Source: {api_name} API\n\n"
        
        # If data is string
        if isinstance(data, str):
            output += data[:4000]
            return output
        
        # If data is dict
        if isinstance(data, dict):
            # Pretty print the JSON
            try:
                formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
                # Limit to 4000 characters
                if len(formatted_json) > 4000:
                    formatted_json = formatted_json[:4000] + "\n... (truncated)"
                return output + f"```json\n{formatted_json}\n```"
            except:
                return output + str(data)[:4000]
        
        # If data is list
        if isinstance(data, list):
            try:
                formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
                if len(formatted_json) > 4000:
                    formatted_json = formatted_json[:4000] + "\n... (truncated)"
                return output + f"```json\n{formatted_json}\n```"
            except:
                return output + str(data)[:4000]
        
        # Fallback
        return output + str(data)[:4000]

# Initialize API
vehicle_api = VehicleAPI()

# ==================== BOT COMMANDS ====================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """
🚗 Vehicle Information Bot

Features:
- Dual API Failover System
- Primary + Backup APIs
- Auto-switch if one fails

How to use:
/vehicle HR26EV0001

Commands:
/start - Show menu
/vehicle [number] - Get info
/help - Help
/status - Check APIs
/apis - List APIs
"""
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
📚 Help

/vehicle HR26EV0001 - Get vehicle info
/status - Check API status
/apis - List all APIs

Supported formats:
- HR26EV0001
- Up14BC4321
- Any Indian vehicle number
"""
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['status'])
def cmd_status(message):
    status_msg = "🔍 API Status Check\n\n"
    
    for endpoint in API_ENDPOINTS:
        status_msg += f"{endpoint['name']} API:\n"
        status_msg += f"URL: {endpoint['url']}\n"
        
        try:
            test_vehicle = "HR26EV0001"
            response = requests.get(f"{endpoint['url']}{test_vehicle}", timeout=5)
            
            if response.status_code == 200:
                status_msg += "Status: ✅ Online\n"
                status_msg += f"Response: {len(response.text)} bytes\n"
            else:
                status_msg += f"Status: ⚠️ Error (HTTP {response.status_code})\n"
        except Exception as e:
            status_msg += f"Status: ❌ Error\n"
        
        status_msg += "\n"
    
    status_msg += f"Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    bot.reply_to(message, status_msg)

@bot.message_handler(commands=['apis'])
def cmd_apis(message):
    apis_text = "📡 Configured APIs\n\n"
    
    for endpoint in API_ENDPOINTS:
        apis_text += f"{endpoint['name']} API (Priority {endpoint['priority']})\n"
        apis_text += f"URL: {endpoint['url']}\n"
        apis_text += f"Timeout: {endpoint['timeout']}s\n\n"
    
    apis_text += "Failover Logic:\n"
    apis_text += "1️⃣ Try Primary API first\n"
    apis_text += "2️⃣ If fails, try Backup API\n"
    apis_text += "3️⃣ If both fail, show error"
    
    bot.reply_to(message, apis_text)

@bot.message_handler(commands=['vehicle'])
def cmd_vehicle(message):
    try:
        command_parts = message.text.split(maxsplit=1)
        
        if len(command_parts) < 2:
            bot.reply_to(message, "❌ Enter vehicle number.\nExample: /vehicle HR26EV0001")
            return
        
        vehicle_number = command_parts[1].strip().upper().replace(" ", "")
        
        if not vehicle_number:
            bot.reply_to(message, "❌ Enter valid vehicle number.")
            return
        
        loading_msg = bot.reply_to(
            message,
            f"🔍 Searching for: {vehicle_number}\n⏳ Trying Primary API..."
        )
        
        result = vehicle_api.fetch_vehicle_data(vehicle_number)
        formatted_data = vehicle_api.format_vehicle_data(result)
        
        # Send without markdown to avoid parsing errors
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
                f"🔍 Searching for: {text}\n⏳ Trying Primary API..."
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
                "❓ Unknown.\nUse /help to see commands."
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
👑 Admin Panel

Commands:
/status - Check APIs
/apis - List APIs

Bot Status: ✅ Running
"""
    bot.reply_to(message, admin_text)

@bot.message_handler(func=lambda message: True)
def default_handler(message):
    bot.reply_to(
        message,
        "❓ Unknown.\nUse /help to see commands."
    )

# ==================== MAIN ====================

def main():
    print("""
    ╔═══════════════════════════════════════════════╗
    ║   VEHICLE BOT v2.1 - JSON PARSING FIX        ║
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