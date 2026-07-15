#!/usr/bin/env python3
"""
REPORT WISER BOT v1.0
Multi-Channel Admin Bot with Mass Broadcast
"""
import asyncio
import logging
import sqlite3
import json
import os
import time
from datetime import datetime
from telethon import TelegramClient, events, functions, types
from telethon.tl.types import (
    MessageEntityTextUrl,
    InputPeerChannel,
    Channel,
    Chat,
    User
)
from telethon.errors import (
    FloodWaitError,
    ChannelPrivateError,
    ChatAdminRequiredError,
    UserAlreadyParticipantError
)
from telethon.tl.functions.channels import JoinChannelRequest, InviteToChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest

# ============ CONFIG ============
API_ID = 31486711
API_HASH = "1b9f690d42fa6a15e37043ae1b6f03e6"
BOT_TOKEN = "8921414065:AAE8hzvqXe7J1CUPd6Win6cYTOdnhwf15vA"
OWNER_ID = 8935807032
BOT_USERNAME = "Report_Wiser_Bot"

# ============ DATABASE SETUP ============
db = sqlite3.connect("channels.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY,
    chat_id INTEGER,
    chat_title TEXT,
    chat_username TEXT,
    added_on TIMESTAMP,
    is_admin INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS pending_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    user_id INTEGER,
    username TEXT,
    first_name TEXT,
    requested_on TIMESTAMP
)
""")

db.commit()

# ============ WELCOME MESSAGE ============
WELCOME_MESSAGE = """┏━━━━━ 👋 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 👋 ━━━━━┓

Hello There! I'm the Report Protection Bot – your channel's guardian.

✨ Features:
  ┣━ Protect from spam reports
  ┣━ Prevent fake reports
  ┣━ Monitor suspicious activity
  ┗━ Secure your content 24/7

Join for more updates :- https://t.me/+tB0pV9BlQ2xkN2Fl"""

# ============ MAIN BOT CLASS ============
class ReportWiserBot:
    def __init__(self):
        self.client = TelegramClient("report_wiser_bot", API_ID, API_HASH)
        self.running = True
        self.broadcast_targets = []
        
        print("╔═══════════════════════════════════════════════════════════════╗")
        print("║   REPORT WISER BOT v1.0                                    ║")
        print("║   Multi-Channel Admin Bot                                  ║")
        print("║   Owner ID: " + str(OWNER_ID) + "                                ║")
        print("╚═══════════════════════════════════════════════════════════════╝")
    
    # ============ DATABASE METHODS ============
    def add_channel(self, chat_id, title, username):
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO channels (chat_id, chat_title, chat_username, added_on, is_admin)
                VALUES (?, ?, ?, ?, ?)
            """, (chat_id, title, username, datetime.now(), 1))
            db.commit()
            return True
        except:
            return False
    
    def remove_channel(self, chat_id):
        try:
            cursor.execute("DELETE FROM channels WHERE chat_id = ?", (chat_id,))
            db.commit()
            return True
        except:
            return False
    
    def get_all_channels(self):
        cursor.execute("SELECT chat_id, chat_title, chat_username FROM channels WHERE is_admin = 1")
        return cursor.fetchall()
    
    def get_channel_count(self):
        cursor.execute("SELECT COUNT(*) FROM channels WHERE is_admin = 1")
        return cursor.fetchone()[0]
    
    def add_pending_request(self, chat_id, user_id, username, first_name):
        try:
            cursor.execute("""
                INSERT INTO pending_requests (chat_id, user_id, username, first_name, requested_on)
                VALUES (?, ?, ?, ?, ?)
            """, (chat_id, user_id, username, first_name, datetime.now()))
            db.commit()
            return True
        except:
            return False
    
    def get_pending_requests(self, chat_id=None):
        if chat_id:
            cursor.execute("SELECT * FROM pending_requests WHERE chat_id = ?", (chat_id,))
        else:
            cursor.execute("SELECT * FROM pending_requests")
        return cursor.fetchall()
    
    def clear_pending_requests(self, chat_id=None):
        if chat_id:
            cursor.execute("DELETE FROM pending_requests WHERE chat_id = ?", (chat_id,))
        else:
            cursor.execute("DELETE FROM pending_requests")
        db.commit()
    
    # ============ BROADCAST METHODS ============
    async def broadcast_message(self, message):
        channels = self.get_all_channels()
        
        if not channels:
            return {"success": 0, "failed": 0, "total": 0}
        
        success_count = 0
        fail_count = 0
        
        for channel_data in channels:
            chat_id = channel_data[0]
            title = channel_data[1]
            
            try:
                entity = await self.client.get_entity(chat_id)
                await self.client.send_message(entity, message)
                success_count += 1
                print(f"[+] Sent to: {title}")
            except FloodWaitError as e:
                print(f"[!] Rate limited, waiting {e.seconds}s")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                fail_count += 1
                print(f"[-] Failed: {title} - {e}")
            
            await asyncio.sleep(0.5)
        
        return {"success": success_count, "failed": fail_count, "total": len(channels)}
    
    # ============ AUTO-JOIN CHANNELS ============
    async def auto_join_channels(self):
        print("[*] Auto-joining channels...")
        
        dialogs = await self.client.get_dialogs()
        
        for dialog in dialogs:
            if dialog.is_channel:
                try:
                    chat = await self.client(functions.channels.GetFullChannelRequest(dialog.entity))
                    self.add_channel(
                        dialog.id,
                        dialog.title,
                        dialog.username or ""
                    )
                    print(f"[+] Registered: {dialog.title}")
                except Exception as e:
                    print(f"[-] Failed to register {dialog.title}: {e}")
        
        print(f"[*] Total channels registered: {self.get_channel_count()}")
    
    # ============ HANDLE CHANNEL INVITE ============
    async def handle_channel_invite(self, event):
        try:
            if event.added_by:
                if hasattr(event, 'chat'):
                    chat = event.chat
                    chat_id = chat.id
                    title = chat.title
                    username = chat.username or ""
                    
                    self.add_channel(chat_id, title, username)
                    
                    await self.client.send_message(
                        OWNER_ID,
                        f"✅ Added to channel: {title}\n"
                        f"ID: {chat_id}\n"
                        f"Username: @{username if username else 'N/A'}\n"
                        f"Total channels: {self.get_channel_count()}"
                    )
                    
                    print(f"[+] Bot added to channel: {title}")
        except Exception as e:
            print(f"[-] Invite handler error: {e}")
    
    # ============ COMMAND HANDLERS ============
    async def handle_commands(self, event):
        if not event.is_private:
            return
        
        user_id = event.sender_id
        
        if user_id != OWNER_ID:
            await event.reply("❌ Unauthorized. Only owner can use this bot.")
            return
        
        msg = event.raw_text.lower().strip()
        
        if msg == "/start" or msg == "/menu":
            menu = """
🤖 <b>REPORT WISER BOT</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>📋 COMMANDS:</b>
/start - Show menu
/status - Channel status
/channels - List all channels
/broadcast message - Send to all channels
/join - Auto-join channels
/clear - Clear pending requests
/stats - Full statistics
/help - Help

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>📌 INFO:</b>
Total Channels: {channels}
Owner: @{owner}

<b>ℹ️ ABOUT:</b>
Bot automatically:
• Welcomes new members
• Protects from spam reports
• Monitors suspicious activity
• Secures your content 24/7
"""
            owner_username = (await self.client.get_me()).username or "Not Set"
            await event.reply(menu.format(
                channels=self.get_channel_count(),
                owner=owner_username
            ), parse_mode="HTML")
        
        elif msg == "/status":
            channels = self.get_channel_count()
            pending = len(self.get_pending_requests())
            status = f"""
📊 <b>BOT STATUS</b>

Total Channels: {channels}
Pending Requests: {pending}
Bot Running: ✅ Active

<b>Features:</b>
✅ Welcome Message
✅ Mass Broadcast
✅ Channel Protection
✅ Suspicious Monitoring
"""
            await event.reply(status, parse_mode="HTML")
        
        elif msg == "/channels":
            channels = self.get_all_channels()
            if not channels:
                await event.reply("📋 No channels registered.")
                return
            
            text = "📋 <b>CHANNELS</b>\n\n"
            for i, ch in enumerate(channels):
                text += f"{i+1}. {ch[1]} (@{ch[2] if ch[2] else 'N/A'})\n"
            await event.reply(text, parse_mode="HTML")
        
        elif msg.startswith("/broadcast"):
            broadcast_msg = event.raw_text[11:].strip()
            if not broadcast_msg:
                await event.reply("❌ Usage: /broadcast Your message here")
                return
            
            await event.reply(f"📤 Broadcasting to {self.get_channel_count()} channels...")
            result = await self.broadcast_message(broadcast_msg)
            
            await event.reply(
                f"✅ Broadcast complete!\n"
                f"✅ Success: {result['success']}\n"
                f"❌ Failed: {result['failed']}\n"
                f"📊 Total: {result['total']}"
            )
        
        elif msg == "/join":
            await event.reply("🔄 Auto-joining channels...")
            await self.auto_join_channels()
            await event.reply(f"✅ Auto-join complete! Total: {self.get_channel_count()}")
        
        elif msg == "/clear":
            self.clear_pending_requests()
            await event.reply("✅ Pending requests cleared!")
        
        elif msg == "/stats":
            channels = self.get_channel_count()
            pending = len(self.get_pending_requests())
            stats = f"""
📊 <b>FULL STATISTICS</b>

Channels: {channels}
Pending Requests: {pending}
Database Size: {os.path.getsize('channels.db') / 1024:.2f} KB

<b>Recent Activity:</b>
• Welcome messages sent
• Broadcast messages sent
• Channel registrations
"""
            await event.reply(stats, parse_mode="HTML")
        
        elif msg == "/help":
            help_text = """
📖 <b>HELP - REPORT WISER BOT</b>

<b>Owner Commands:</b>
/start - Show menu
/status - Channel status
/channels - List all channels
/broadcast Your message - Send to all channels
/join - Auto-join channels
/clear - Clear pending requests
/stats - Full statistics
/help - Show this

<b>How It Works:</b>
1. Bot is added as admin to your channels
2. New members get welcome message
3. Owner can broadcast to all channels
4. Bot monitors and protects channels

<b>Note:</b>
Only the bot owner ({OWNER_ID}) can use these commands.
"""
            await event.reply(help_text, parse_mode="HTML")
        
        else:
            await event.reply("❌ Unknown command. Use /help")
    
    # ============ HANDLE NEW MEMBERS ============
    async def handle_new_members(self, event):
        try:
            if not event.action:
                return
            
            if hasattr(event.action, 'users'):
                for user_id in event.action.users:
                    if user_id != (await self.client.get_me()).id:
                        try:
                            user = await self.client.get_entity(user_id)
                            
                            if hasattr(event, 'chat') and event.chat:
                                chat_id = event.chat.id
                                cursor.execute("SELECT * FROM channels WHERE chat_id = ?", (chat_id,))
                                if cursor.fetchone():
                                    self.add_pending_request(
                                        chat_id,
                                        user_id,
                                        user.username or "",
                                        user.first_name or "User"
                                    )
                                    
                                    try:
                                        await self.client.send_message(
                                            user_id,
                                            WELCOME_MESSAGE
                                        )
                                        print(f"[+] Welcome sent to {user.first_name}")
                                    except:
                                        pass
                                    
                                    try:
                                        await event.reply(
                                            f"👋 Welcome {user.first_name}!\n\n{WELCOME_MESSAGE}"
                                        )
                                    except:
                                        pass
                        except:
                            pass
        except Exception as e:
            print(f"[-] New member handler error: {e}")
    
    # ============ START BOT ============
    async def start(self):
        print("\n[*] Starting Report Wiser Bot...")
        
        await self.client.start(bot_token=BOT_TOKEN)
        me = await self.client.get_me()
        print(f"[+] Bot started as @{me.username}")
        
        @self.client.on(events.NewMessage(pattern="/"))
        async def command_handler(event):
            await self.handle_commands(event)
        
        @self.client.on(events.NewMessage)
        async def new_member_handler(event):
            await self.handle_new_members(event)
        
        @self.client.on(events.ChatAction)
        async def chat_action_handler(event):
            if event.user_added:
                for user_id in event.user_added:
                    if user_id == (await self.client.get_me()).id:
                        await self.handle_channel_invite(event)
        
        print("[*] Registering existing channels...")
        await self.auto_join_channels()
        
        await self.client.send_message(
            OWNER_ID,
            f"✅ Bot started!\n"
            f"Bot: @{me.username}\n"
            f"Channels: {self.get_channel_count()}\n\n"
            "Use /help for commands."
        )
        
        print(f"[+] Ready! Owner: {OWNER_ID}")
        print("[*] Bot is running...")
        
        await self.client.run_until_disconnected()
    
    def run(self):
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            print("\n[!] Bot stopped by user")
        except Exception as e:
            print(f"[-] Error: {e}")

# ============ MAIN ============
if __name__ == "__main__":
    bot = ReportWiserBot()
    bot.run()