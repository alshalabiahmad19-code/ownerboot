import asyncio
import os
import threading
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer

import discord
from discord.ext import commands
import yt_dlp

class HealthHandler(BaseHTTPRequestHandler):
def do_GET(self):
self.send_response(200)
self.send_header("Content-Type", "text/plain; charset=utf-8")
self.end_headers()
self.wfile.write(b"ownerboot is running!")

```
def log_message(self, format, *args):
    pass
```

def start_web_server():
port = int(os.getenv("PORT", "10000"))
server = HTTPServer(("0.0.0.0", port), HealthHandler)
server.serve_forever()

threading.Thread(
target=start_web_server,
daemon=True
).start()

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(
command_prefix="!",
intents=intents
)

OWNER_SERVER_ID = 1267380491703812107
OWNER_VOICE_CHANNEL_ID = 1548094091798257806

queues = {}

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

```
def __init__(self, source, *, data):
    super().__init__(source, volume=0.5)
    self.data = data
    self.title = data.get("title", "Unknown")

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
                item for item in data["entries"]
                if item
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
```

async def get_owner_channel(guild):

```
if guild.id != OWNER_SERVER_ID:
    print(
        f"[VOICE] Wrong guild: {guild.id}"
    )
    return None

print(
    f"[VOICE] Looking for channel "
    f"{OWNER_VOICE_CHANNEL_ID}"
)

channel = guild.get_channel(
    OWNER_VOICE_CHANNEL_ID
)

if channel is None:

    print(
        "[VOICE] Channel not in cache. "
        "Fetching from Discord..."
    )

    try:
        channel = await bot.fetch_channel(
            OWNER_VOICE_CHANNEL_ID
        )

    except Exception as e:

        print(
            f"[VOICE] Fetch failed: "
            f"{type(e).__name__}: {e}"
        )

        traceback.print_exc()

        return None

print(
    f"[VOICE] Found channel: "
    f"{channel.name} "
    f"({channel.id}) "
    f"type={channel.type}"
)

if not isinstance(
    channel,
    discord.VoiceChannel
):

    print(
        "[VOICE] Channel is not a normal "
        "voice channel."
    )

    return None

return channel
```

async def connect_owner(guild):

```
print(
    f"[VOICE] Connection requested "
    f"for guild {guild.id}"
)

if guild.id != OWNER_SERVER_ID:
    return None

channel = await get_owner_channel(
    guild
)

if channel is None:

    print(
        "[VOICE] Owner voice channel "
        "could not be found."
    )

    return None

voice = guild.voice_client

try:

    if voice and voice.is_connected():

        print(
            f"[VOICE] Already connected to "
            f"{voice.channel.name}"
        )

        if voice.channel.id != channel.id:

            print(
                "[VOICE] Moving to owner channel..."
            )

            await voice.move_to(channel)

        return voice

    print(
        "[VOICE] Connecting to owner channel..."
    )

    voice = await channel.connect(
        reconnect=True,
        timeout=30
    )

    print(
        f"[VOICE] SUCCESS: Connected to "
        f"{channel.name}"
    )

    return voice

except Exception as e:

    print(
        "[VOICE] VOICE CONNECTION FAILED"
    )

    print(
        f"[VOICE] Error type: "
        f"{type(e).__name__}"
    )

    print(
        f"[VOICE] Error: {e}"
    )

    traceback.print_exc()

    return None
```

def user_in_owner_channel(message):

```
if not message.author.voice:
    return False

return (
    message.author.voice.channel.id
    == OWNER_VOICE_CHANNEL_ID
)
```

def get_queue(guild_id):

```
return queues.setdefault(
    guild_id,
    []
)
```

async def play_next(
guild,
text_channel
):

```
queue = get_queue(
    guild.id
)

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
                f"[FFMPEG] Error: {error}"
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
        f"🎵 **تشغيل التالي:** "
        f"`{player.title}`"
    )

except Exception as e:

    print(
        f"[PLAY NEXT] "
        f"{type(e).__name__}: {e}"
    )

    traceback.print_exc()

    await text_channel.send(
        "❌ تعذر تشغيل الأغنية."
    )

    if queue:
        await play_next(
            guild,
            text_channel
        )
```

@bot.event
async def on_ready():

```
print(
    "========================================"
)

print(
    f"✅ ownerboot logged in as {bot.user}"
)

print(
    f"✅ Bot ID: {bot.user.id}"
)

print(
    f"✅ Connected guilds: {len(bot.guilds)}"
)

print(
    f"👑 Server ID: {OWNER_SERVER_ID}"
)

print(
    f"👑 Voice Channel ID: "
    f"{OWNER_VOICE_CHANNEL_ID}"
)

print(
    "========================================"
)

guild = bot.get_guild(
    OWNER_SERVER_ID
)

if guild is None:

    print(
        "[READY] Owner server was not found."
    )

    return

print(
    f"[READY] Owner server found: "
    f"{guild.name}"
)

await connect_owner(
    guild
)
```

@bot.event
async def on_voice_state_update(
member,
before,
after
):

```
if not bot.user:
    return

if member.id != bot.user.id:
    return

if member.guild.id != OWNER_SERVER_ID:
    return

print(
    f"[VOICE STATE] "
    f"Before: {before.channel} | "
    f"After: {after.channel}"
)

if (
    after.channel is None
    or after.channel.id != OWNER_VOICE_CHANNEL_ID
):

    await asyncio.sleep(2)

    await connect_owner(
        member.guild
    )
```

@bot.event
async def on_message(message):

```
if message.author.bot:
    return

content = message.content.strip()

if content.startswith("ش "):

    print(
        f"[COMMAND] Play requested by "
        f"{message.author}"
    )

    query = content[2:].strip()

    if not query:

        await message.channel.send(
            "❌ اكتب اسم الأغنية.\n"
            "مثال: `ش Faded`"
        )

        return

    if not user_in_owner_channel(message):

        print(
            "[COMMAND] User is not in "
            "owner voice channel."
        )

        await message.channel.send(
            "🔒 لازم تكون داخل روم الأونرات "
            "حتى تستخدم البوت."
        )

        return

    print(
        "[COMMAND] User is in owner "
        "voice channel."
    )

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
                    f"[FFMPEG] Error: {error}"
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
            f"[PLAY] Error: "
            f"{type(e).__name__}: {e}"
        )

        traceback.print_exc()

        await message.channel.send(
            "❌ صار خطأ أثناء تحميل الأغنية."
        )

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

await bot.process_commands(
    message
)
```

token = os.getenv(
"DISCORD_TOKEN"
)

if not token:

```
raise RuntimeError(
    "DISCORD_TOKEN غير موجود."
)
```

print(
"🚀 Starting ownerboot..."
)

bot.run(
token
)
