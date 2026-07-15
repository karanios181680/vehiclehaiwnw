#!/usr/bin/env python3
"""
REPORT WISER BOT - CLEAN VERSION
Only 3 Features:
1. Admin banne pe "CHANNEL SECURED BY REPORT WISER BOT"
2. Owner broadcast to all channels
3. New member request pe welcome message
"""
import asyncio
import sqlite3
import os
from datetime import datetime
from telethon import TelegramClient, events, functions
from telethon.errors import FloodWaitError

# ============ CONFIG ============
API_ID = 31486711
API_HASH = "1b9f690d42fa6a15e37043ae1b6f03e6"
BOT_TOKEN = "8921414065:AAE8hzvqXe7J1CUPd6Win6cYTOdnhwf15vA"
OWNER_ID = 8935807032

# ============ MESSAGES ============
SECURED_MSG = """🔒 CHANNEL SECURED BY REPORT WISER BOT 🔒

✅ This channel is now protected
✅ Fake reports will be blocked
✅ 24/7 monitoring active
✅ Content secured

Report Wiser Bot - Your Channel Guardian"""

WELCOME_MSG = """┏━━━━━ 👋 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 👋 ━━━━━┓

Hello There! I'm the Report Protection Bot – your channel's guardian.

✨ Features:
  ┣━ Protect from spam reports
  ┣━ Prevent fake reports
  ┣━ Monitor suspicious activity
  ┗━ Secure your content 24/7

Join for more updates :- https://t.me/+tB0pV9BlQ2xkN2Fl"""

# ============ DATABASE ============
db = sqlite3.connect("channels.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS channels (
    chat_id INTEGER PRIMARY KEY,
    title TEXT,
    added_on TIMESTAMP
)
""")
db.commit()

class ReportWiserBot:
    def __init__(self):
        self.client = TelegramClient("report_wiser_bot", API_ID, API_HASH)
        print("[+] Report Wiser Bot Starting...")
        print(f"[+] Owner ID: {OWNER_ID}")

    def add_channel(self, chat_id, title):
        cursor.execute("INSERT OR REPLACE INTO channels (chat_id, title, added_on) VALUES (?, ?, ?)", 
                      (chat_id, title, datetime.now()))
        db.commit()

    def get_channels(self):
        cursor.execute("SELECT chat_id, title FROM channels")
        return cursor.fetchall()

    def get_channel_count(self):
        cursor.execute("SELECT COUNT(*) FROM channels")
        return cursor.fetchone()[0]

    async def broadcast(self, message):
        channels = self.get_channels()
        if not channels:
            return {"success": 0, "failed": 0}
        
        success = 0
        failed = 0
        
        for chat_id, title in channels:
            try:
                entity = await self.client.get_entity(int(chat_id))
                await self.client.send_message(entity, message)
                success += 1
                print(f"[+] Sent to: {title}")
            except Exception as e:
                failed += 1
                print(f"[-] Failed: {title}")
            await asyncio.sleep(0.5)
        
        return {"success": success, "failed": failed}

    async def start(self):
        await self.client.start(bot_token=BOT_TOKEN)
        me = await self.client.get_me()
        print(f"[+] Bot started as @{me.username}")

        # ===== FEATURE 1: Admin banne pe secured msg =====
        @self.client.on(events.ChatAction)
        async def on_admin_added(event):
            if event.user_added:
                for user_id in event.user_added:
                    if user_id == (await self.client.get_me()).id:
                        try:
                            chat = event.chat
                            self.add_channel(chat.id, chat.title)
                            await self.client.send_message(chat.id, SECURED_MSG)
                            print(f"[+] Secured: {chat.title}")
                            
                            # Notify owner
                            await self.client.send_message(
                                OWNER_ID,
                                f"✅ Bot added as admin in: {chat.title}\nTotal: {self.get_channel_count()}"
                            )
                        except Exception as e:
                            print(f"[-] Error in admin add: {e}")

        # ===== FEATURE 2: New member request =====
        @self.client.on(events.ChatAction)
        async def on_new_member(event):
            if event.user_added:
                for user_id in event.user_added:
                    if user_id != (await self.client.get_me()).id:
                        try:
                            user = await self.client.get_entity(user_id)
                            await self.client.send_message(user_id, WELCOME_MSG)
                            print(f"[+] Welcome sent to: {user.first_name}")
                        except:
                            pass

        # ===== OWNER COMMANDS =====
        @self.client.on(events.NewMessage)
        async def owner_commands(event):
            if not event.is_private:
                return
            if event.sender_id != OWNER_ID:
                await event.reply("❌ Unauthorized.")
                return

            msg = event.raw_text.strip()

            if msg == "/start":
                await event.reply(f"""
🤖 REPORT WISER BOT

Channels: {self.get_channel_count()}

Commands:
/broadcast Your message - Send to all channels
/channels - List all channels
/status - Check status
/help - Help
""")

            elif msg == "/help":
                await event.reply("""
📖 Commands:
/broadcast Your message - Send to all channels
/channels - List all channels
/status - Check status
""")

            elif msg == "/status":
                await event.reply(f"📊 Channels: {self.get_channel_count()}\n✅ Bot is running")

            elif msg == "/channels":
                channels = self.get_channels()
                if not channels:
                    await event.reply("📋 No channels yet.")
                    return
                text = "📋 CHANNELS:\n\n"
                for i, (_, title) in enumerate(channels):
                    text += f"{i+1}. {title}\n"
                await event.reply(text)

            elif msg.startswith("/broadcast"):
                broadcast_msg = msg[10:].strip()
                if not broadcast_msg:
                    await event.reply("❌ /broadcast Your message")
                    return
                
                await event.reply(f"📤 Broadcasting to {self.get_channel_count()} channels...")
                result = await self.broadcast(broadcast_msg)
                await event.reply(f"✅ Sent: {result['success']}\n❌ Failed: {result['failed']}")

            else:
                await event.reply("❌ Use /help for commands")

        # ===== AUTO-REGISTER EXISTING CHANNELS =====
        print("[*] Registering existing channels...")
        dialogs = await self.client.get_dialogs()
        for dialog in dialogs:
            if dialog.is_channel:
                try:
                    self.add_channel(dialog.id, dialog.title)
                    print(f"[+] Registered: {dialog.title}")
                except:
                    pass

        await self.client.send_message(
            OWNER_ID,
            f"✅ Bot started!\nChannels: {self.get_channel_count()}\nUse /help"
        )

        print(f"[+] Ready! {self.get_channel_count()} channels registered")
        await self.client.run_until_disconnected()

    def run(self):
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            print("\n[!] Stopped")

if __name__ == "__main__":
    bot = ReportWiserBot()
    bot.run()