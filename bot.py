#!/usr/bin/env python3
"""
Vehicle Information Bot - API Based
Version: 1.0.0
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
import threading

# ==================== CONFIG ====================
BOT_TOKEN = "8815661182:AAHMa-UX5hH0dmqgvgPuMGOf5797psYg6hk"
ADMIN_IDS = [8935807032, 7934015451]
API_BASE_URL = "http://72.61.242.185:2000/DL10CN5594"

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
        self.base_url = API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Connection': 'keep-alive'
        })
    
    def fetch_vehicle_data(self, vehicle_number):
        """
        Fetch vehicle data from API
        """
        try:
            # Clean vehicle number
            vehicle_number = vehicle_number.upper().strip()
            vehicle_number = re.sub(r'\s+', '', vehicle_number)
            
            # Build URL
            url = f"{self.base_url}{vehicle_number}"
            
            logger.info(f"Fetching data for: {vehicle_number}")
            logger.info(f"URL: {url}")
            
            # Make request
            response = self.session.get(url, timeout=30)
            
            # Check response
            if response.status_code == 200:
                try:
                    data = response.json()
                    return {
                        'success': True,
                        'data': data,
                        'raw': response.text
                    }
                except json.JSONDecodeError:
                    # If response is not JSON, return as text
                    return {
                        'success': True,
                        'data': response.text,
                        'raw': response.text,
                        'is_json': False
                    }
            else:
                return {
                    'success': False,
                    'error': f"API returned status: {response.status_code}",
                    'status_code': response.status_code
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': "Request timed out. API may be slow or down."
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': "Cannot connect to API. Server may be down."
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error: {str(e)}"
            }
    
    def format_vehicle_data(self, result):
        """
        Format vehicle data for display
        """
        if not result.get('success'):
            return f"â **Error:** {result.get('error', 'Unknown error')}"
        
        data = result.get('data')
        
        # If data is a string (not JSON)
        if isinstance(data, str):
            return f"ð **Vehicle Data:**\n\n```\n{data[:4000]}\n```"
        
        # If data is JSON
        if isinstance(data, dict):
            formatted = f"ð **Vehicle Information**\n\n"
            
            # Format all key-value pairs
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    formatted += f"\n**{key}:**\n```\n{json.dumps(value, indent=2, ensure_ascii=False)[:500]}\n```"
                else:
                    formatted += f"**{key}:** {value}\n"
            
            return formatted
        
        # If data is list
        if isinstance(data, list):
            formatted = f"ð **Vehicle Data** ({len(data)} items)\n\n"
            for i, item in enumerate(data):
                formatted += f"**{i+1}.** {item}\n"
            return formatted
        
        # Fallback
        return f"ð **Data:**\n```\n{json.dumps(data, indent=2, ensure_ascii=False)[:4000]}\n```"

# Initialize API
vehicle_api = VehicleAPI()

# ==================== BOT COMMANDS ====================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """
ð **Vehicle Information Bot**

**How to use:**

/vehicle [VEHICLE_NUMBER]

**Example:**
`/vehicle PB65AM0008`

**Commands:**
/start - Show this menu
/vehicle [number] - Get vehicle info
/help - Detailed help
/status - Check API status
/about - About this bot

**Note:** Enter vehicle number without spaces.
"""
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
ð **Detailed Help**

**/vehicle [NUMBER]**
- Fetches vehicle information
- Example: `/vehicle HR26EV0003`
- Enter number without spaces

**/status**
- Check if API is working

**/about**
- About this bot

**Supported Formats:**
- PB65AM0008
- HR26EV0003
- Any Indian vehicle number

**Data Provided:**
- All information available in API
- Response in JSON format
- Vehicle registration details
"""
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['status'])
def cmd_status(message):
    """Check API status"""
    status_msg = "ð **Checking API Status...**\n\n"
    
    try:
        # Test with a sample vehicle number
        test_vehicle = "HR26EV0003"
        response = requests.get(f"{API_BASE_URL}{test_vehicle}", timeout=10)
        
        status_msg += f"**API URL:** `{API_BASE_URL}`\n"
        status_msg += f"**Status Code:** {response.status_code}\n"
        
        if response.status_code == 200:
            status_msg += "**Status:** â Online\n"
            status_msg += f"**Response Size:** {len(response.text)} bytes\n"
            
            # Try to parse JSON
            try:
                data = response.json()
                status_msg += f"**Data Type:** JSON\n"
                status_msg += f"**Keys:** {', '.join(data.keys())[:50]}...\n"
            except:
                status_msg += f"**Data Type:** Text\n"
                status_msg += f"**Preview:** {response.text[:100]}...\n"
        else:
            status_msg += "**Status:** â ï¸ Warning\n"
            status_msg += f"API returned non-200 status.\n"
        
    except requests.exceptions.Timeout:
        status_msg += "**Status:** â Timeout\n"
        status_msg += "API is not responding.\n"
    except requests.exceptions.ConnectionError:
        status_msg += "**Status:** â Connection Error\n"
        status_msg += "Cannot connect to API.\n"
    except Exception as e:
        status_msg += f"**Status:** â Error\n"
        status_msg += f"Error: {str(e)}\n"
    
    status_msg += f"\nð Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    bot.reply_to(message, status_msg, parse_mode='Markdown')

@bot.message_handler(commands=['about'])
def cmd_about(message):
    about_text = """
ð¤ **Vehicle Information Bot**

**Version:** 1.0.0
**Type:** API-Based Vehicle Lookup

**Features:**
- Vehicle number search
- API integration
- JSON data formatting
- Multi-user support

**Admin:** @[YourUsername]
**Support:** Contact bot owner

**API Source:** NexGenMp
"""
    bot.reply_to(message, about_text, parse_mode='Markdown')

@bot.message_handler(commands=['vehicle'])
def cmd_vehicle(message):
    """Handle /vehicle command"""
    try:
        # Extract vehicle number from command
        command_parts = message.text.split(maxsplit=1)
        
        if len(command_parts) < 2:
            bot.reply_to(
                message,
                "â **Please enter a vehicle number.**\n\n"
                "Usage: `/vehicle PB65AM0008`\n\n"
                "Example: `/vehicle HR26EV0003`",
                parse_mode='Markdown'
            )
            return
        
        vehicle_number = command_parts[1].strip().upper()
        vehicle_number = re.sub(r'\s+', '', vehicle_number)
        
        if not vehicle_number:
            bot.reply_to(
                message,
                "â **Please enter a valid vehicle number.**",
                parse_mode='Markdown'
            )
            return
        
        # Send loading message
        loading_msg = bot.reply_to(
            message,
            f"ð **Searching for vehicle:** `{vehicle_number}`\n\nâ³ Please wait...",
            parse_mode='Markdown'
        )
        
        # Fetch data
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
        
        # Log successful lookup
        logger.info(f"Vehicle lookup: {vehicle_number} - User: {message.from_user.id}")
        
    except Exception as e:
        bot.reply_to(
            message,
            f"â **Error:** {str(e)}",
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
            # It's a vehicle number
            vehicle_number = text
            
            # Send loading message
            loading_msg = bot.reply_to(
                message,
                f"ð **Searching for vehicle:** `{vehicle_number}`\n\nâ³ Please wait...",
                parse_mode='Markdown'
            )
            
            # Fetch data
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
            
            logger.info(f"Vehicle lookup: {vehicle_number} - User: {message.from_user.id}")
        else:
            # Send help if not a command
            bot.reply_to(
                message,
                "â **Unknown command.**\n\n"
                "Use:\n"
                "`/vehicle PB65AM0008` - Get vehicle info\n"
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
        bot.reply_to(message, "â You are not authorized to use this command.")
        return
    
    admin_text = """
ð **Admin Panel**

**Commands:**
/status - Check API status
/broadcast [message] - Send to all users
/users - Show user count
/restart - Restart bot (simulated)

**API Status:** â Online
**Bot Status:** â Running
"""
    bot.reply_to(message, admin_text, parse_mode='Markdown')

@bot.message_handler(commands=['broadcast'])
def cmd_broadcast(message):
    """Broadcast message to all users"""
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "â You are not authorized to use this command.")
        return
    
    # This is a placeholder - implement if needed
    bot.reply_to(message, "ð¢ Broadcast feature (to be implemented)")

# ==================== ERROR HANDLER ====================

@bot.message_handler(func=lambda message: True)
def default_handler(message):
    """Handle unknown commands"""
    bot.reply_to(
        message,
        "â Unknown command.\n\n"
        "Use `/help` to see available commands.",
        parse_mode='Markdown'
    )

# ==================== MAIN ====================

def main():
    print("""
    âââââââââââââââââââââââââââââââââââââââââââââââââ
    â   VEHICLE INFORMATION BOT v1.0               â
    â   - API Based Vehicle Lookup                 â
    â   - Quick Search                            â
    â   - JSON Data Formatter                     â
    âââââââââââââââââââââââââââââââââââââââââââââââââ
    """)
    
    print(f"â Bot token: {BOT_TOKEN[:10]}...")
    print(f"â Admin IDs: {ADMIN_IDS}")
    print(f"â API URL: {API_BASE_URL}")
    print(f"â Bot starting...")
    
    try:
        bot.polling(none_stop=True, interval=1)
    except Exception as e:
        print(f"â Error: {str(e)}")
        time.sleep(5)
        main()

if __name__ == "__main__":
    main()