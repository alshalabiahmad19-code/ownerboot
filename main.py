import os
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import discord
from discord.ext import commands
import yt_dlp

TOKEN = os.getenv("DISCORD_TOKEN")

OWNER_VOICE_CHANNEL_ID = 1548094091798257806
GUILD_ID = 1267380491703812107

class HealthHandler(BaseHTTPRequestHandler):
def do_GET(self):
self.send_response(200)
self.send_header("Content-Type", "text/plain")
self.end_headers()
self.wfile.write(b"ownerboot is running")

```
def log_message(self, format, *args):
    return
```

def start_health_server():
port = int(os.getenv("PORT", "10000"))
server = HTTPServer(("0.0.0.0", port), HealthHandler)
server.serve_forever()

threading.Thread(target=start_health_server, daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(
command_prefix="!",
intents=intents,
help_command=None
)

async def connect_to_owner_channel():
await bot.wait_until_ready()

```
while not bot.is_closed():
    try:
        channel = bot.get_channel(OWNER_VOICE_CHANNEL_ID)

        if channel is None:
            print("Channel not found in cache. Trying fetch_channel...")
            channel = await bot.fetch_channel(OWNER_VOICE_CHANNEL_ID)

        print(f"Voice channel found: {channel.name}")

        if not isinstance(channel, discord.VoiceChannel):
            print("ERROR: The ID is not a normal voice channel.")
            return

        if channel.guild.id != GUILD_ID:
            print("ERROR: Voice channel is in the wrong server.")
            return

        voice_client = discord.utils.get(
            bot.voice_clients,
            guild=channel.guild
        )

        if voice_client is None:
            print("Connecting to owner voice channel...")
            await channel.connect(self_deaf=True)
            print("Successfully connected to owner voice channel.")

        elif voice_client.channel.id != channel.id:
            print("Moving bot to owner voice channel...")
            await voice_client.move_to(channel)
            print("Successfully moved to owner voice channel.")

        else:
            print("Bot is already in the owner voice channel.")

        return

    except discord.Forbidden as e:
        print("ERROR: Discord denied permission to join the voice channel.")
        print(e)
        return

    except discord.HTTPException as e:
        print("ERROR: Discord HTTP error while joining voice channel.")
        print(e)

    except Exception as e:
        print("ERROR while joining voice channel:")
        print(repr(e))

    await asyncio.sleep(10)
```

@bot.event
async def on_ready():
print("----------------------------------------")
print(f"Logged in as: {bot.user}")
print(f"Bot ID: {bot.user.id}")
print(f"Server ID: {GUILD_ID}")
print(f"Owner voice channel ID: {OWNER_VOICE_CHANNEL_ID}")
print("----------------------------------------")

```
bot.loop.create_task(connect_to_owner_channel())
```

@bot.event
async def on_message(message):
if message.author.bot:
return

```
if message.guild is None:
    return

if message.guild.id != GUILD_ID:
    return

content = message.content.strip()

if content.startswith("ش "):
    if not message.author.voice:
        await message.reply("لازم تكون داخل روم الأونرات.")
        return

    if message.author.voice.channel.id != OWNER_VOICE_CHANNEL_ID:
        await message.reply("أوامر الأغاني تعمل فقط داخل روم الأونرات.")
        return

    query = content[2:].strip()

    if not query:
        await message.reply("اكتب اسم الأغنية بعد ش.")
        return

    voice = discord.utils.get(
        bot.voice_clients,
        guild=message.guild
    )

    if voice is None:
        try:
            channel = await bot.fetch_channel(OWNER_VOICE_CHANNEL_ID)
            voice = await channel.connect(self_deaf=True)
        except Exception as e:
            print("VOICE CONNECT ERROR:", repr(e))
            await message.reply("البوت لم يستطع دخول روم الأونرات.")
            return

    if voice.channel.id != OWNER_VOICE_CHANNEL_ID:
        await voice.move_to(message.author.voice.channel)

    try:
        ytdl_options = {
            "format": "bestaudio/best",
            "noplaylist": True,
            "quiet": True,
            "default_search": "ytsearch",
            "source_address": "0.0.0.0",
        }

        with yt_dlp.YoutubeDL(ytdl_options) as ydl:
            info = ydl.extract_info(query, download=False)

        if "entries" in info:
            info = info["entries"][0]

        audio_url = info["url"]
        title = info.get("title", "Unknown")

        if voice.is_playing():
            voice.stop()

        source = discord.FFmpegPCMAudio(
            audio_url,
            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            options="-vn"
        )

        voice.play(source)

        await message.reply(f"▶️ شغلت: **{title}**")

    except Exception as e:
        print("PLAY ERROR:", repr(e))
        await message.reply("صار خطأ أثناء تشغيل الأغنية.")

elif content == "س":
    if not message.author.voice:
        await message.reply("لازم تكون داخل روم الأونرات.")
        return

    if message.author.voice.channel.id != OWNER_VOICE_CHANNEL_ID:
        await message.reply("الأمر يعمل فقط داخل روم الأونرات.")
        return

    voice = discord.utils.get(
        bot.voice_clients,
        guild=message.guild
    )

    if voice and voice.is_playing():
        voice.stop()
        await message.reply("⏭️ تم تخطي الأغنية.")
    else:
        await message.reply("ما في أغنية شغالة.")

elif content == "وقف":
    if not message.author.voice:
        await message.reply("لازم تكون داخل روم الأونرات.")
        return

    if message.author.voice.channel.id != OWNER_VOICE_CHANNEL_ID:
        await message.reply("الأمر يعمل فقط داخل روم الأونرات.")
        return

    voice = discord.utils.get(
        bot.voice_clients,
        guild=message.guild
    )

    if voice:
        if voice.is_playing():
            voice.stop()

        await voice.disconnect()
        await message.reply("⏹️ تم إيقاف الأغنية وخروج البوت من الروم.")
```

if not TOKEN:
raise RuntimeError("DISCORD_TOKEN environment variable is missing.")

bot.run(TOKEN)
