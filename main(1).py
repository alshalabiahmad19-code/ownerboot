import os
import asyncio
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
import discord
from discord.ext import commands
import yt_dlp

TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_VOICE_CHANNEL_ID = 1548094091798257806
GUILD_ID = 1267380491703812107

threading.Thread(target=lambda: HTTPServer(("0.0.0.0", int(os.getenv("PORT", "10000"))), SimpleHTTPRequestHandler).serve_forever(), daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

async def connect_owner():
    await bot.wait_until_ready()
    try:
        channel = bot.get_channel(OWNER_VOICE_CHANNEL_ID) or await bot.fetch_channel(OWNER_VOICE_CHANNEL_ID)
        print(f"Found channel: {channel.name} | Guild: {channel.guild.id}")
        if channel.guild.id != GUILD_ID or not isinstance(channel, discord.VoiceChannel):
            print("ERROR: Wrong server or channel type")
            return
        voice = discord.utils.get(bot.voice_clients, guild=channel.guild)
        if voice is None:
            await channel.connect(self_deaf=True)
            print("SUCCESS: Connected to owner voice channel.")
        elif voice.channel.id != channel.id:
            await voice.move_to(channel)
            print("SUCCESS: Moved to owner voice channel.")
        else:
            print("Bot is already in owner voice channel.")
    except Exception as e:
        print("VOICE CONNECT ERROR:", repr(e))

@bot.event
async def on_ready():
    print("OWNERBOOT ONLINE")
    print("Bot:", bot.user)
    await connect_owner()

@bot.event
async def on_message(message):
    if message.author.bot or message.guild is None or message.guild.id != GUILD_ID:
        return
    content = message.content.strip()
    if not content.startswith(("ش ", "س", "وقف")):
        return
    if not message.author.voice or message.author.voice.channel.id != OWNER_VOICE_CHANNEL_ID:
        await message.reply("لازم تكون داخل روم الأونرات.")
        return
    if content.startswith("ش "):
        query = content[2:].strip()
        if not query:
            await message.reply("اكتب اسم الأغنية بعد ش.")
            return
        voice = discord.utils.get(bot.voice_clients, guild=message.guild)
        if voice is None:
            try:
                channel = await bot.fetch_channel(OWNER_VOICE_CHANNEL_ID)
                voice = await channel.connect(self_deaf=True)
            except Exception as e:
                print("VOICE CONNECT ERROR:", repr(e))
                await message.reply("البوت لم يستطع دخول روم الأونرات.")
                return
        try:
            opts = {"format": "bestaudio/best", "noplaylist": True, "quiet": True, "default_search": "ytsearch", "source_address": "0.0.0.0"}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(query, download=False)
            if "entries" in info:
                info = info["entries"][0]
            source = discord.FFmpegPCMAudio(info["url"], before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", options="-vn")
            if voice.is_playing():
                voice.stop()
            voice.play(source)
            await message.reply(f"▶️ شغلت: **{info.get('title', 'Unknown')}**")
        except Exception as e:
            print("PLAY ERROR:", repr(e))
            await message.reply("صار خطأ أثناء تشغيل الأغنية.")
    elif content == "س":
        voice = discord.utils.get(bot.voice_clients, guild=message.guild)
        if voice and voice.is_playing():
            voice.stop()
            await message.reply("⏭️ تم تخطي الأغنية.")
        else:
            await message.reply("ما في أغنية شغالة.")
    elif content == "وقف":
        voice = discord.utils.get(bot.voice_clients, guild=message.guild)
        if voice:
            if voice.is_playing():
                voice.stop()
            await voice.disconnect()
        await message.reply("⏹️ تم إيقاف الأغنية وخروج البوت من الروم.")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN environment variable is missing")
bot.run(TOKEN)
