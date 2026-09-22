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

def health_response(self):
self.send_response(200)
self.send_header("Content-Type", "text/plain")
self.end_headers()
self.wfile.write(b"ownerboot is running")

HealthHandler = type(
"HealthHandler",
(BaseHTTPRequestHandler,),
{
"do_GET": health_response,
"log_message": lambda self, format, *args: None
}
)

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
try:
    channel = bot.get_channel(OWNER_VOICE_CHANNEL_ID)

    if channel is None:
        print("Channel not in cache, fetching...")
        channel = await bot.fetch_channel(OWNER_VOICE_CHANNEL_ID)

    print("Found channel:", channel.name)
    print("Channel ID:", channel.id)
    print("Guild ID:", channel.guild.id)

    if channel.guild.id != GUILD_ID:
        print("ERROR: Wrong server.")
        return

    if not isinstance(channel, discord.VoiceChannel):
        print("ERROR: This is not a voice channel.")
        return

    voice = discord.utils.get(
        bot.voice_clients,
        guild=channel.guild
    )

    if voice is None:
        print("Connecting to owner voice channel...")
        await channel.connect(self_deaf=True)
        print("SUCCESS: Connected to owner voice channel.")

    elif voice.channel.id != channel.id:
        print("Moving to owner voice channel...")
        await voice.move_to(channel)
        print("SUCCESS: Moved to owner voice channel.")

    else:
        print("Bot is already inside owner voice channel.")

except discord.Forbidden as e:
    print("ERROR: Missing Discord permissions.")
    print(repr(e))

except Exception as e:
    print("ERROR CONNECTING TO VOICE:")
    print(repr(e))
```

@bot.event
async def on_ready():
print("================================")
print("OWNERBOOT ONLINE")
print("Bot:", bot.user)
print("Bot ID:", bot.user.id)
print("Server ID:", GUILD_ID)
print("Voice ID:", OWNER_VOICE_CHANNEL_ID)
print("================================")

```
await connect_to_owner_channel()
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
        await message.reply("الأوامر تعمل فقط داخل روم الأونرات.")
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

    try:
        ytdl_options = {
            "format": "bestaudio/best",
            "noplaylist": True,
            "quiet": True,
            "default_search": "ytsearch",
            "source_address": "0.0.0.0"
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
raise RuntimeError("DISCORD_TOKEN environment variable is missing")

bot.run(TOKEN)
