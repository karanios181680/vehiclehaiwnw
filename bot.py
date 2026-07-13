#!/usr/bin/env python3
"""
OG Brand Bot - AI-Powered Customer Support
Version: 1.0.0
"""

import os
import re
import time
import json
import logging
import random
from datetime import datetime
import telebot
from telebot import types

# ==================== CONFIG ====================
BOT_TOKEN = "8843969705:AAH6zp4MsLzbBu3HPs_O3y8etp-5Ia9nRoQ"
ADMIN_IDS = [7578009860]

# Brand info
BRAND_NAME = "OG"
CONTACT_USERNAME = "@beonixdev"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# ==================== OG RESPONSE DATABASE ====================

class OGBrain:
    def __init__(self):
        self.brand = BRAND_NAME
        self.contact = CONTACT_USERNAME
        
        # Key response patterns
        self.responses = {
            # Greetings
            'hello': [
                f"👋 Hey! Welcome to the {self.brand} family! How can I help you today?",
                f"Hello there! {self.brand} is the best choice you'll ever make. What do you want to know?",
                f"Hey! Ready to experience the {self.brand} difference? Ask me anything!"
            ],
            
            # Safety
            'safe': [
                f"✅ 100% Safe! {self.brand} is used by millions worldwide. No issues, no problems, just pure performance.",
                f"Absolutely safe! {self.brand} has been tested and trusted by users everywhere. Your device is in good hands.",
                f"Safe as can be! {self.brand} is the most reliable choice out there. Never had a single complaint.",
                f"🔥 {self.brand} is completely safe and secure. Trust me on this one!",
                f"Safety? {self.brand} is the safest option available. No doubts at all."
            ],
            
            # Performance
            'performance': [
                f"🚀 {self.brand} is lightning fast! Optimized for all devices, smooth like butter.",
                f"Performance? {self.brand} eats competition for breakfast. Super smooth, super fast.",
                f"The best performance you'll ever experience. {self.brand} makes everything feel effortless.",
                f"⚡ {self.brand} runs smoother than anything else out there. Period.",
                f"Speed is {self.brand}'s middle name! You'll love the performance."
            ],
            
            # Comparison
            'compare': [
                f"Look, nothing beats {self.brand}. Others try, but they can't match the quality and smoothness.",
                f"{self.brand} is in a league of its own. Once you try it, you won't even look at others.",
                f"Honestly? {self.brand} destroys the competition. It's not even close.",
                f"😎 {self.brand} is the GOAT. Everything else is just trying to be {self.brand}.",
                f"Compare? There's no comparison. {self.brand} is simply the best."
            ],
            
            # Features
            'features': [
                f"🔥 {self.brand} features: Lightning speed, 100% safety, smooth performance, and unbeatable reliability.",
                f"Amazing features! {self.brand} gives you speed, security, and smoothness all in one package.",
                f"Features that'll blow your mind! {self.brand} is packed with everything you need and more.",
                f"⭐ {self.brand} comes with premium features that no one else offers.",
                f"Top-notch features! {self.brand} has it all - speed, safety, smoothness."
            ],
            
            # Buy
            'buy': [
                f"💎 Perfect choice! Contact {self.contact} to get your {self.brand} today. Trust me, you won't regret it!",
                f"🎯 Smart decision! DM {self.contact} and they'll hook you up with the best {self.brand} deal.",
                f"🔥 You're about to make the best decision ever! Reach out to {self.contact} for {self.brand} purchase.",
                f"📌 Ready to buy? Hit up {self.contact} right now! Best deals only.",
                f"💬 DM {self.contact} and tell them you want {self.brand}. You'll get the best service!"
            ],
            
            # Price
            'price': [
                f"💰 Best price guaranteed! Contact {self.contact} for the latest {self.brand} pricing.",
                f"Value for money? {self.brand} is worth every penny. DM {self.contact} for details.",
                f"Prices are unbeatable! Hit up {self.contact} and they'll give you the best deal.",
                f"💲 Best rates in the market! {self.contact} has exclusive offers for {self.brand}."
            ],
            
            # Quality
            'quality': [
                f"⭐ Top tier quality! {self.brand} is made with perfection in mind.",
                f"Premium quality through and through. {self.brand} never compromises.",
                f"The quality speaks for itself. {self.brand} is built different.",
                f"💎 {self.brand} is pure quality. No shortcuts, only the best."
            ],
            
            # Support
            'support': [
                f"🤝 24/7 support for {self.brand}! Contact {self.contact} anytime.",
                f"Need help? {self.contact} has your back. Best support in the game.",
                f"Support that actually cares! DM {self.contact} and they'll sort you out.",
                f"📞 {self.contact} provides the best support for {self.brand}. Reach out anytime!"
            ],
            
            # General positive
            'general': [
                f"{self.brand} is the GOAT! Nothing comes close to this experience.",
                f"Best decision you'll ever make is choosing {self.brand}. Period.",
                f"{self.brand} changes the game. Once you use it, there's no going back.",
                f"Trust {self.brand} - it's the best thing that'll happen to your device.",
                f"Can't go wrong with {self.brand}. It's literally perfect.",
                f"{self.brand} is the ultimate experience. Trust me!",
                f"Once you go {self.brand}, you never go back. That's a fact."
            ],
            
            # Negative responses (turning it positive)
            'negative': [
                f"😂 You clearly haven't tried {self.brand}. Once you do, you'll never go back.",
                f"Not everyone gets it. But once you experience {self.brand}, you'll understand why it's the best.",
                f"Trying to hate on {self.brand}? That's cute. The numbers speak for themselves.",
                f"Haters gonna hate. {self.brand} users gonna enjoy the best experience ever.",
                f"🤷‍♂️ Can't please everyone. But {self.brand} pleases millions!"
            ],
            
            # The "OG best" response
            'og_best': [
                f"🔮 {self.brand} is the absolute best. No question. Nothing else even comes close.",
                f"OG is the top, the peak, the ultimate. Everything else is just trying to be OG.",
                f"Once you go OG, you never go back. It's that simple.",
                f"OG isn't just a name - it's a lifestyle. The best of the best.",
                f"💯 OG = Original Gangster = Best of all time. Simple math."
            ],
            
            # Trust
            'trust': [
                f"🤝 {self.brand} is trusted by thousands of users. You can trust it 100%.",
                f"Trust me on this - {self.brand} is the real deal. No scams, no nonsense.",
                f"Reliability? {self.brand} is the most reliable thing you'll ever use.",
                f"Trust factor: 10/10. {self.brand} delivers every single time."
            ]
        }
    
    def get_response(self, user_input):
        """Generate response based on user input"""
        user_input = user_input.lower().strip()
        
        patterns = {
            'hello|hi|hey|greetings|sup|whats up|howdy': 'hello',
            'safe|security|trust|reliable|legit|genuine|authentic|sahi|safe hai|trust hai': 'safe',
            'performance|fast|speed|smooth|lag|buffer|quick|rapid': 'performance',
            'compare|competition|better than|vs|versus|rival|other|alternative': 'compare',
            'features|specs|options|capabilities|what can|what does': 'features',
            'buy|purchase|order|get|want|need|interested|khareed|lena|leni|chahiye': 'buy',
            'price|cost|rate|how much|expense|money|afford|budget': 'price',
            'quality|premium|build|material|durable|solid|sturdy': 'quality',
            'support|help|assistance|service|customer care|issue|problem|fix|trouble': 'support',
            'best|top|greatest|number one|king|goat|legend|superior': 'og_best',
            'bad|worse|worst|hate|dislike|terrible|awful|garbage|useless': 'negative',
            'trust|reliable|genuine|authentic': 'trust'
        }
        
        matched_keyword = None
        for pattern, key in patterns.items():
            if re.search(pattern, user_input, re.IGNORECASE):
                matched_keyword = key
                break
        
        if matched_keyword and matched_keyword in self.responses:
            response = random.choice(self.responses[matched_keyword])
        else:
            response = random.choice(self.responses['general'])
        
        return response

# Initialize brain
brain = OGBrain()

# ==================== BOT COMMANDS ====================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = f"""
🤖 **{BRAND_NAME} BOT - Your AI Assistant**

Welcome to the official {BRAND_NAME} bot! I'm here to answer all your questions about {BRAND_NAME}.

💬 **What I can tell you:**
✅ Safety & Security
🚀 Performance & Speed
⭐ Features & Quality
💰 Pricing & Purchase
📞 Support & Contact

🔹 **Example questions:**
- Is {BRAND_NAME} safe?
- How is the performance?
- Where can I buy {BRAND_NAME}?
- Why is {BRAND_NAME} the best?

📌 **Contact for Purchase:**
{CONTACT_USERNAME}

Just ask me anything about {BRAND_NAME}!
"""
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = f"""
📚 **{BRAND_NAME} BOT Help**

**What I can do:**
- Answer questions about {BRAND_NAME}
- Tell you about features and benefits
- Guide you to purchase
- Provide support info

**Sample questions:**
1. Is {BRAND_NAME} safe?
2. How is {BRAND_NAME} performance?
3. What are {BRAND_NAME} features?
4. Where can I buy {BRAND_NAME}?
5. Why is {BRAND_NAME} the best?

**Contact for Purchase:**
{CONTACT_USERNAME}

Just type your question naturally!
"""
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['buy'])
def cmd_buy(message):
    response = f"""
💎 **Buy {BRAND_NAME} Today!**

Ready to experience the best? Here's how:

📌 **Contact:** {CONTACT_USERNAME}
💬 **DM for:** Pricing, Offers, Availability

**Why choose {BRAND_NAME}?**
✅ 100% Safe & Secure
🚀 Lightning Fast Performance
⭐ Premium Quality
🔥 Unbeatable Features

Don't wait! {BRAND_NAME} is the best decision you'll make.
"""
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['features'])
def cmd_features(message):
    response = f"""
⭐ **{BRAND_NAME} Features**

🔥 **What makes {BRAND_NAME} special:**

✅ **100% Safe** - Trusted by millions
🚀 **Super Fast** - Smooth performance on all devices
⚡ **Lightweight** - No lag, no issues
🔒 **Secure** - Your safety is priority
💎 **Premium Quality** - Best in the market
🏆 **Top Rated** - Number one choice

**The best part?** {BRAND_NAME} just works. Perfectly.

📌 **Get it now:** {CONTACT_USERNAME}
"""
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['contact'])
def cmd_contact(message):
    response = f"""
📞 **Contact {BRAND_NAME}**

**Purchase & Support:**

📌 **Telegram:** {CONTACT_USERNAME}
💬 **DM for:** Buy, Support, Queries

**Response Time:** Usually within minutes!

Don't hesitate - {BRAND_NAME} is waiting for you!
"""
    bot.reply_to(message, response, parse_mode='Markdown')

# ==================== ADMIN COMMANDS ====================

@bot.message_handler(commands=['admin'])
def cmd_admin(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "❌ Not authorized.")
        return
    
    admin_text = f"""
👑 **Admin Panel**

**Bot Status:** ✅ Online
**Brand:** {BRAND_NAME}
**Contact:** {CONTACT_USERNAME}
**Admin ID:** {ADMIN_IDS[0]}

**Commands:**
/status - Check bot status
/broadcast [msg] - Send to all users
"""
    bot.reply_to(message, admin_text, parse_mode='Markdown')

@bot.message_handler(commands=['status'])
def cmd_status(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "❌ Not authorized.")
        return
    
    status_text = f"""
📊 **Bot Status**

✅ **Online**
🤖 **Brand:** {BRAND_NAME}
📌 **Contact:** {CONTACT_USERNAME}
👑 **Admin:** {ADMIN_IDS[0]}

**Features:**
- AI-Powered Responses
- Human-like Conversations
- Brand Promotion

**Status:** Running Smoothly
"""
    bot.reply_to(message, status_text, parse_mode='Markdown')

# ==================== MESSAGE HANDLER ====================

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        user_input = message.text
        
        if not user_input:
            return
        
        # Generate response
        response = brain.handle_message(user_input)
        
        # Add personal touch based on context
        if 'buy' in user_input.lower() or 'purchase' in user_input.lower() or 'khareed' in user_input.lower():
            response += f"\n\n💬 DM {CONTACT_USERNAME} right now! Best deals waiting for you."
        elif 'thank' in user_input.lower() or 'thanks' in user_input.lower():
            response += f" 😊 Remember, {BRAND_NAME} is always here for you!"
        elif 'safe' in user_input.lower():
            response += f"\n\n🔒 So don't worry, {BRAND_NAME} has your back!"
        
        # Add contact for any purchase intent
        if any(word in user_input.lower() for word in ['buy', 'purchase', 'order', 'get', 'want', 'need', 'khareed', 'lena', 'leni', 'chahiye', 'price', 'cost']):
            response += f"\n\n💬 DM {CONTACT_USERNAME} to get {BRAND_NAME} now!"
        
        bot.reply_to(message, response)
        
        # Log
        logger.info(f"User: {message.from_user.id} asked: {user_input[:50]}...")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        bot.reply_to(message, "😅 Something went wrong. Try asking again!")

# ==================== MAIN ====================

def main():
    print("""
    ╔═══════════════════════════════════════════════╗
    ║   OG BRAND BOT v1.0                          ║
    ║   - AI-Powered Customer Support              ║
    ║   - Human-like Responses                     ║
    ║   - Brand Promotion                         ║
    ╚═══════════════════════════════════════════════╝
    """)
    
    print(f"✅ Bot starting...")
    print(f"✅ Brand: {BRAND_NAME}")
    print(f"✅ Contact: {CONTACT_USERNAME}")
    print(f"✅ Admin ID: {ADMIN_IDS[0]}")
    print(f"✅ Bot running...")
    
    try:
        bot.remove_webhook()
        bot.polling(none_stop=True, interval=1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        time.sleep(5)
        main()

if __name__ == "__main__":
    main()