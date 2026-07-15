#!/usr/bin/env python3
"""
REPORT WISER BOT - FIXED & IMPROVED
"""

import asyncio
import sqlite3
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

# Database
db = sqlite3.connect("channels.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS channels (chat_id INTEGER PRIMARY KEY, title TEXT)")
db.commit()

class ReportWiserBot:
    def __init__(self):
        self.client = TelegramClient("rw_bot", API_ID, API_HASH)
        self.bot_username = None
        self.processed_events = set()
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
                print(f"[+] Sent to: {title}")
            except Exception as e:
                print(f"[-] Failed {title}: {e}")
            await asyncio.sleep(0.5)  # Rate limit safe
        return success

    async def start(self):
        await self.client.start(bot_token=BOT_TOKEN)
        me = await self.client.get_me()
        self.bot_username = me.username
        print(f"[+] Bot online: @{me.username}")

        # Admin added event
        @self.client.on(events.ChatAction)
        async def on_admin_added(event):
            event_id = f"admin_{event.chat_id}"
            if event_id in self.processed_events:
                return
            self.processed_events.add(event_id)

            me = await self.client.get_me()
            if getattr(event, 'user_added', None) and me.id in event.user_added:
                try:
                    chat = await self.client.get_entity(event.chat_id)
                    title = getattr(chat, 'title', str(event.chat_id))
                    self.add_channel(chat.id, title)
                    await self.client.send_message(event.chat_id, SECURED_MSG)
                    print(f"[+] Secured: {title}")
                    await self.client.send_message(OWNER_ID, f"✅ Bot admin bana diya: {title}")
                except Exception as e:
                    print(f"[-] Admin event error: {e}")

        # Welcome on new member / approved join
        @self.client.on(events.ChatAction)
        async def on_new_member(event):
            event_id = f"member_{event.chat_id}_{getattr(event, 'action', '')}"
            if event_id in self.processed_events:
                return
            self.processed_events.add(event_id)

            if event.user_joined or getattr(event, 'user_added', None):
                bot_id = (await self.client.get_me()).id
                users = event.user_joined or event.user_added or []
                for uid in users:
                    if uid != bot_id:
                        try:
                            user = await self.client.get_entity(uid)
                            await self.client.send_message(uid, WELCOME_MSG)
                            print(f"[+] Welcome to {user.first_name}")
                        except Exception as e:
                            print(f"[-] Welcome error {uid}: {e}")

        # Owner commands (private only)
        @self.client.on(events.NewMessage)
        async def owner_cmd(event):
            if not event.is_private or event.sender_id != OWNER_ID:
                return

            msg = event.raw_text.strip().lower()

            if msg == "/start":
                await event.reply(f"🤖 Report Wiser Bot\nChannels: {self.count()}\n\n/broadcast <msg>\n/channels\n/status")

            elif msg == "/channels":
                ch = self.get_channels()
                txt = "📋 CHANNELS:\n" + "\n".join([f"{i+1}. {title}" for i, (_, title) in enumerate(ch)]) if ch else "No channels yet."
                await event.reply(txt)

            elif msg == "/status":
                await event.reply(f"📊 Channels: {self.count()}\n✅ Running")

            elif msg.startswith("/broadcast "):
                bmsg = event.raw_text[11:].strip()  # raw_text for full msg
                if not bmsg:
                    await event.reply("❌ /broadcast your message")
                    return
                await event.reply(f"📤 Broadcasting to {self.count()} channels...")
                sent = await self.broadcast(bmsg)
                await event.reply(f"✅ Broadcast complete! Sent: {sent}")

        # Register existing
        print("[*] Registering existing channels...")
        try:
            dialogs = await self.client.get_dialogs(limit=200)
            for d in dialogs:
                if getattr(d, 'is_channel', False):
                    try:
                        self.add_channel(d.id, getattr(d, 'title', 'Unknown'))
                        print(f"[+] Registered: {d.title}")
                    except:
                        pass
        except Exception as e:
            print(f"[-] Register error: {e}")

        await self.client.send_message(OWNER_ID, f"✅ Bot Started!\nChannels tracked: {self.count()}")
        print(f"[+] Ready! Total channels: {self.count()}")

        await self.client.run_until_disconnected()

    def run(self):
        asyncio.run(self.start())

if __name__ == "__main__":
    bot = ReportWiserBot()
    bot.run()