```python
import asyncio
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import discord
from discord.ext import commands
import yt_dlp


# =========================
# Render health check
# =========================

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OwnerBot is running!")

    def log_message(self, format, *args):
        pass


def start_web_server():
    port = int(os.getenv("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


threading.Thread(
    target=start_web_server,
    daemon=True
).start()


# =========================
# Discord
# =========================

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


# =========================
# Owner voice channel
# =========================

OWNER_VOICE_CHANNEL_ID = 1548094091798257806


# Queue per server
queues = {}


# =========================
# YouTube
# =========================

YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch1",
    "source_address": "0.0.0.0",
}

FFMPEG_OPTIONS = {
    "before_options": (
        "-reconnect 1 "
        "-reconnect_streamed 1 "
        "-reconnect_delay_max 5"
    ),
    "options": "-vn",
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)


class YouTubeSource(discord.PCMVolumeTransformer):

    def __init__(self, source, *, data):
        super().__init__(source, volume=0.5)
        self.data = data
        self.title = data.get(
            "title",
            "Unknown"
        )

    @classmethod
    async def from_query(cls, query):

        loop = asyncio.get_running_loop()

        def extract():

            data = ytdl.extract_info(
                query,
                download=False
            )

            if not data:
                raise RuntimeError(
                    "YouTube لم يرجع نتيجة."
                )

            if "entries" in data:

                entries = [
                    x for x in data["entries"]
                    if x
                ]

                if not entries:
                    raise RuntimeError(
                        "لم يتم العثور على الأغنية."
                    )

                data = entries[0]

            return data

        data = await loop.run_in_executor(
            None,
            extract
        )

        url = data.get("url")

        if not url:
            raise RuntimeError(
                "لم يتم الحصول على رابط الصوت."
            )

        ffmpeg = os.getenv(
            "FFMPEG_PATH",
            "ffmpeg"
        )

        source = discord.FFmpegPCMAudio(
            url,
            executable=ffmpeg,
            **FFMPEG_OPTIONS
        )

        return cls(
            source,
            data=data
        )


# =========================
# Voice
# =========================

def get_owner_channel(guild):

    channel = guild.get_channel(
        OWNER_VOICE_CHANNEL_ID
    )

    if isinstance(
        channel,
        discord.VoiceChannel
    ):
        return channel

    return None


async def connect_owner(guild):

    channel = get_owner_channel(guild)

    if channel is None:
        print(
            f"❌ Owner voice channel "
            f"{OWNER_VOICE_CHANNEL_ID} "
            f"was not found."
        )
        return None

    voice = guild.voice_client

    try:

        if voice and voice.is_connected():

            if voice.channel.id != channel.id:
                await voice.move_to(channel)

            return voice

        return await channel.connect(
            reconnect=True
        )

    except Exception as e:

        print(
            f"❌ Voice connection error: "
            f"{type(e).__name__}: {e}"
        )

        return None


def user_in_owner_channel(message):

    if not message.author.voice:
        return False

    channel = message.author.voice.channel

    return (
        channel.id == OWNER_VOICE_CHANNEL_ID
    )


# =========================
# Queue
# =========================

def get_queue(guild_id):

    return queues.setdefault(
        guild_id,
        []
    )


async def play_next(
    guild,
    text_channel
):

    queue = get_queue(guild.id)

    voice = guild.voice_client

    if not queue:
        return

    if not voice:
        return

    if not voice.is_connected():
        return

    query = queue.pop(0)

    try:

        player = await YouTubeSource.from_query(
            query
        )

        def finished(error):

            if error:
                print(
                    f"FFmpeg error: {error}"
                )

            asyncio.run_coroutine_threadsafe(
                play_next(
                    guild,
                    text_channel
                ),
                bot.loop
            )

        voice.play(
            player,
            after=finished
        )

        await text_channel.send(
            f"🎵 **تشغيل التالي:** `{player.title}`"
        )

    except Exception as e:

        print(
            f"Play next error: "
            f"{type(e).__name__}: {e}"
        )

        await text_channel.send(
            "❌ تعذر تشغيل الأغنية.\n"
            f"`{type(e).__name__}: {e}`"
        )

        if queue:
            await play_next(
                guild,
                text_channel
            )


# =========================
# Ready
# =========================

@bot.event
async def on_ready():

    print(
        f"✅ OwnerBot logged in as "
        f"{bot.user}"
    )

    print(
        f"👑 Owner voice channel: "
        f"{OWNER_VOICE_CHANNEL_ID}"
    )

    for guild in bot.guilds:
        await connect_owner(guild)


# =========================
# Keep bot in Owner room
# =========================

@bot.event
async def on_voice_state_update(
    member,
    before,
    after
):

    if not bot.user:
        return

    if member.id != bot.user.id:
        return

    if (
        after.channel is None
        or after.channel.id != OWNER_VOICE_CHANNEL_ID
    ):

        await asyncio.sleep(2)

        await connect_owner(
            member.guild
        )


# =========================
# Messages
# =========================

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    content = message.content.strip()

    # =====================
    # ش SONG
    # =====================

    if content.startswith("ش "):

        query = content[2:].strip()

        if not query:

            await message.channel.send(
                "❌ اكتب اسم الأغنية.\n"
                "مثال: `ش Faded`"
            )

            return

        if not user_in_owner_channel(message):

            await message.channel.send(
                "🔒 لازم تكون داخل روم الأونرات "
                "حتى تستخدم البوت."
            )

            return

        voice = await connect_owner(
            message.guild
        )

        if not voice:

            await message.channel.send(
                "❌ البوت لم يستطع دخول روم الأونرات."
            )

            return

        queue = get_queue(
            message.guild.id
        )

        if (
            voice.is_playing()
            or voice.is_paused()
        ):

            queue.append(query)

            await message.channel.send(
                f"📝 تمت إضافة `{query}` إلى القائمة."
            )

            return

        try:

            async with message.channel.typing():

                player = await YouTubeSource.from_query(
                    query
                )

            def finished(error):

                if error:
                    print(
                        f"FFmpeg error: {error}"
                    )

                asyncio.run_coroutine_threadsafe(
                    play_next(
                        message.guild,
                        message.channel
                    ),
                    bot.loop
                )

            voice.play(
                player,
                after=finished
            )

            await message.channel.send(
                f"🎵 **جاري التشغيل:** "
                f"`{player.title}`"
            )

        except Exception as e:

            print(
                f"❌ Play error: "
                f"{type(e).__name__}: {e}"
            )

            await message.channel.send(
                "❌ صار خطأ أثناء تحميل الأغنية.\n"
                f"`{type(e).__name__}: {e}`"
            )

    # =====================
    # س = Skip
    # =====================

    elif content == "س":

        if not user_in_owner_channel(message):
            return

        voice = message.guild.voice_client

        if voice and voice.is_playing():

            voice.stop()

            await message.channel.send(
                "⏭️ تم تخطي الأغنية."
            )

        else:

            await message.channel.send(
                "❌ لا توجد أغنية تعمل."
            )

    # =====================
    # وقف
    # =====================

    elif content == "وقف":

        if not user_in_owner_channel(message):
            return

        queue = get_queue(
            message.guild.id
        )

        queue.clear()

        voice = message.guild.voice_client

        if voice and (
            voice.is_playing()
            or voice.is_paused()
        ):

            voice.stop()

        await message.channel.send(
            "🛑 تم إيقاف الأغنية ومسح القائمة."
        )

    await bot.process_commands(message)


# =========================
# Start
# =========================

token = os.getenv(
    "DISCORD_TOKEN"
)

if not token:

    raise RuntimeError(
        "DISCORD_TOKEN غير موجود."
    )

bot.run(token)
```
