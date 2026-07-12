#!/usr/bin/env python3
"""
Vehicle Information Bot - Dual API Failover System
Version: 2.0.0
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
        """
        Fetch data from a specific API endpoint
        """
        try:
            # Clean vehicle number
            vehicle_number = vehicle_number.upper().strip()
            vehicle_number = re.sub(r'\s+', '', vehicle_number)
            
            # Build URL
            url = f"{endpoint['url']}{vehicle_number}"
            
            logger.info(f"Trying {endpoint['name']} API: {url}")
            
            # Make request
            response = self.session.get(url, timeout=endpoint['timeout'])
            
            # Check response
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
            return {
                'success': False,
                'error': "Timeout",
                'api': endpoint['name']
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': "Connection Error",
                'api': endpoint['name']
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'api': endpoint['name']
            }
    
    def fetch_vehicle_data(self, vehicle_number):
        """
        Fetch vehicle data with failover - tries primary then backup
        """
        # Try each API endpoint in priority order
        for endpoint in API_ENDPOINTS:
            result = self.fetch_from_api(vehicle_number, endpoint)
            
            if result.get('success'):
                logger.info(f"✅ {endpoint['name']} API returned data for {vehicle_number}")
                return result
            else:
                logger.warning(f"❌ {endpoint['name']} API failed: {result.get('error')}")
                # Continue to next API
        
        # All APIs failed
        return {
            'success': False,
            'error': "All APIs failed. Please try again later.",
            'details': "Primary and Backup APIs are down."
        }
    
    def format_vehicle_data(self, result):
        """
        Format vehicle data for display
        """
        if not result.get('success'):
            return f"❌ **Error:** {result.get('error', 'Unknown error')}\n\n💡 Try again later."
        
        data = result.get('data')
        api_name = result.get('api', 'Unknown')
        
        # Header with API info
        formatted = f"🚗 **Vehicle Information**\n"
        formatted += f"📡 **Source:** {api_name} API\n\n"
        
        # If data is a string (not JSON)
        if isinstance(data, str):
            return formatted + f"📋 **Data:**\n```\n{data[:4000]}\n```"
        
        # If data is JSON
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    formatted += f"\n**{key}:**\n```\n{json.dumps(value, indent=2, ensure_ascii=False)[:500]}\n```"
                else:
                    formatted += f"**{key}:** {value}\n"
            return formatted
        
        # If data is list
        if isinstance(data, list):
            formatted += f"📋 **Data** ({len(data)} items)\n\n"
            for i, item in enumerate(data):
                formatted += f"**{i+1}.** {item}\n"
            return formatted
        
        # Fallback
        return formatted + f"📋 **Data:**\n```\n{json.dumps(data, indent=2, ensure_ascii=False)[:4000]}\n```"

# Initialize API
vehicle_api = VehicleAPI()

# ==================== BOT COMMANDS ====================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """
🚗 **Vehicle Information Bot**

**Features:**
- Dual API Failover System
- Primary + Backup APIs
- Auto-switch if one fails

**How to use:**

/vehicle [VEHICLE_NUMBER]

**Example:**
`/vehicle HR26EV0001`

**Commands:**
/start - Show this menu
/vehicle [number] - Get vehicle info
/help - Detailed help
/status - Check API status
/apis - List all APIs

**Note:** Enter vehicle number without spaces.
"""
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
📚 **Detailed Help**

**/vehicle [NUMBER]**
- Fetches vehicle information
- Example: `/vehicle HR26EV0001`
- Automatically tries backup API if primary fails

**/status**
- Check if APIs are working

**/apis**
- List all configured APIs

**/about**
- About this bot

**Supported Formats:**
- HR26EV0001
- Up14BC4321
- Any Indian vehicle number

**Data Provided:**
- All information available in API
- Response in JSON or text format
- Vehicle registration details

**Failover System:**
- Primary: 161.248.163.233:1080
- Backup: 161.248.163.233:1081
"""
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['status'])
def cmd_status(message):
    """Check API status"""
    status_msg = "🔍 **API Status Check**\n\n"
    
    for endpoint in API_ENDPOINTS:
        status_msg += f"**{endpoint['name']} API:**\n"
        status_msg += f"URL: `{endpoint['url']}`\n"
        
        try:
            # Test with sample vehicle
            test_vehicle = "HR26EV0001"
            response = requests.get(f"{endpoint['url']}{test_vehicle}", timeout=5)
            
            if response.status_code == 200:
                status_msg += "Status: ✅ **Online**\n"
                status_msg += f"Response: {len(response.text)} bytes\n"
            else:
                status_msg += f"Status: ⚠️ **Error** (HTTP {response.status_code})\n"
                
        except requests.exceptions.Timeout:
            status_msg += "Status: ❌ **Timeout**\n"
        except requests.exceptions.ConnectionError:
            status_msg += "Status: ❌ **Connection Error**\n"
        except Exception as e:
            status_msg += f"Status: ❌ **Error** ({str(e)[:30]})\n"
        
        status_msg += "\n"
    
    status_msg += f"📅 Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    bot.reply_to(message, status_msg, parse_mode='Markdown')

@bot.message_handler(commands=['apis'])
def cmd_apis(message):
    """List all APIs"""
    apis_text = "📡 **Configured APIs**\n\n"
    
    for endpoint in API_ENDPOINTS:
        apis_text += f"**{endpoint['name']} API** (Priority {endpoint['priority']})\n"
        apis_text += f"URL: `{endpoint['url']}`\n"
        apis_text += f"Timeout: {endpoint['timeout']}s\n"
        apis_text += "\n"
    
    apis_text += "**Failover Logic:**\n"
    apis_text += "1️⃣ Try Primary API first\n"
    apis_text += "2️⃣ If fails, try Backup API\n"
    apis_text += "3️⃣ If both fail, show error\n"
    
    bot.reply_to(message, apis_text, parse_mode='Markdown')

@bot.message_handler(commands=['about'])
def cmd_about(message):
    about_text = """
🤖 **Vehicle Information Bot**

**Version:** 2.0.0
**Type:** API-Based Vehicle Lookup

**Features:**
- Vehicle number search
- Dual API failover system
- Primary + Backup APIs
- Auto-switch on failure
- JSON data formatting
- Multi-user support

**API Failover:**
- Primary: 161.248.163.233:1080
- Backup: 161.248.163.233:1081

**Admin:** @[YourUsername]
"""
    bot.reply_to(message, about_text, parse_mode='Markdown')

@bot.message_handler(commands=['vehicle'])
def cmd_vehicle(message):
    """Handle /vehicle command"""
    try:
        command_parts = message.text.split(maxsplit=1)
        
        if len(command_parts) < 2:
            bot.reply_to(
                message,
                "❌ **Please enter a vehicle number.**\n\n"
                "Usage: `/vehicle HR26EV0001`\n\n"
                "Example: `/vehicle Up14BC4321`",
                parse_mode='Markdown'
            )
            return
        
        vehicle_number = command_parts[1].strip().upper()
        vehicle_number = re.sub(r'\s+', '', vehicle_number)
        
        if not vehicle_number:
            bot.reply_to(
                message,
                "❌ **Please enter a valid vehicle number.**",
                parse_mode='Markdown'
            )
            return
        
        # Send loading message
        loading_msg = bot.reply_to(
            message,
            f"🔍 **Searching for vehicle:** `{vehicle_number}`\n\n⏳ Trying Primary API...",
            parse_mode='Markdown'
        )
        
        # Fetch data with failover
        result = vehicle_api.fetch_vehicle_data(vehicle_number)
        
        # Format data
        formatted_data = vehicle_api.format_vehicle_data(result)
        
        # Update loading message with API info
        if result.get('success'):
            loading_text = f"🔍 **Searching for vehicle:** `{vehicle_number}`\n\n✅ **Found using {result.get('api', 'Unknown')} API**\n\n"
        else:
            loading_text = f"🔍 **Searching for vehicle:** `{vehicle_number}`\n\n❌ **All APIs failed**\n\n"
        
        # Update message with result
        bot.edit_message_text(
            formatted_data,
            chat_id=message.chat.id,
            message_id=loading_msg.message_id,
            parse_mode='Markdown'
        )
        
        # Log successful lookup
        if result.get('success'):
            logger.info(f"✅ Vehicle lookup: {vehicle_number} - API: {result.get('api')} - User: {message.from_user.id}")
        else:
            logger.warning(f"❌ Vehicle lookup failed: {vehicle_number} - User: {message.from_user.id}")
        
    except Exception as e:
        bot.reply_to(
            message,
            f"❌ **Error:** {str(e)}",
            parse_mode='Markdown'
        )
        logger.error(f"Error in cmd_vehicle: {str(e)}")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    """Handle any message that starts with a vehicle number"""
    try:
        text = message.text.strip().upper()
        
        # Check if message is a vehicle number pattern
        vehicle_pattern = r'^[A-Z]{2}\d{1,2}[A-Z]{1,2}\d{4}$'
        
        if re.match(vehicle_pattern, text):
            vehicle_number = text
            
            # Send loading message
            loading_msg = bot.reply_to(
                message,
                f"🔍 **Searching for vehicle:** `{vehicle_number}`\n\n⏳ Trying Primary API...",
                parse_mode='Markdown'
            )
            
            # Fetch data with failover
            result = vehicle_api.fetch_vehicle_data(vehicle_number)
            
            # Format data
            formatted_data = vehicle_api.format_vehicle_data(result)
            
            # Update message with result
            bot.edit_message_text(
                formatted_data,
                chat_id=message.chat.id,
                message_id=loading_msg.message_id,
                parse_mode='Markdown'
            )
            
            if result.get('success'):
                logger.info(f"✅ Vehicle lookup: {vehicle_number} - API: {result.get('api')} - User: {message.from_user.id}")
            else:
                logger.warning(f"❌ Vehicle lookup failed: {vehicle_number} - User: {message.from_user.id}")
        else:
            bot.reply_to(
                message,
                "❓ Unknown command.\n\n"
                "Use:\n"
                "`/vehicle HR26EV0001` - Get vehicle info\n"
                "`/help` - Show help\n"
                "`/status` - Check API status",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        logger.error(f"Error in handle_text: {str(e)}")

# ==================== ADMIN COMMANDS ====================

@bot.message_handler(commands=['admin'])
def cmd_admin(message):
    """Admin-only commands"""
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return
    
    admin_text = """
👑 **Admin Panel**

**Commands:**
/status - Check API status
/apis - List all APIs
/broadcast [message] - Send to all users

**API Failover Status:** ✅ Active
**Primary:** 161.248.163.233:1080
**Backup:** 161.248.163.233:1081

**Bot Status:** ✅ Running
"""
    bot.reply_to(message, admin_text, parse_mode='Markdown')

@bot.message_handler(commands=['broadcast'])
def cmd_broadcast(message):
    """Broadcast message to all users"""
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return
    
    bot.reply_to(message, "📢 Broadcast feature (to be implemented)")

@bot.message_handler(func=lambda message: True)
def default_handler(message):
    """Handle unknown commands"""
    bot.reply_to(
        message,
        "❓ Unknown command.\n\n"
        "Use `/help` to see available commands.",
        parse_mode='Markdown'
    )

# ==================== MAIN ====================

def main():
    print("""
    ╔═══════════════════════════════════════════════╗
    ║   VEHICLE INFORMATION BOT v2.0               ║
    ║   - Dual API Failover System                 ║
    ║   - Primary + Backup APIs                    ║
    ║   - Auto-switch on failure                   ║
    ╚═══════════════════════════════════════════════╝
    """)
    
    print(f"✅ Bot token: {BOT_TOKEN[:10]}...")
    print(f"✅ Admin IDs: {ADMIN_IDS}")
    print(f"✅ APIs Configured: {len(API_ENDPOINTS)}")
    for api in API_ENDPOINTS:
        print(f"   - {api['name']}: {api['url']}")
    print(f"✅ Bot starting...")
    
    try:
        bot.polling(none_stop=True, interval=1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        time.sleep(5)
        main()

if __name__ == "__main__":
    main()