# INSTALL pynacl, discord, ytdlp
import discord
from discord.ext import commands
import yt_dlp
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

FFMPEG_OPTIONS = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': True}

class MusicBot(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.queue = []

    @commands.command()
    async def play(self, ctx, *, search):
        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        if not voice_channel:
            return await ctx.send("You're not in a voice channel!")
        if not ctx.voice_client:
            await voice_channel.connect()
        async with ctx.typing():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(f"ytsearch:{search}", download=False)
                if 'entries' in info:
                    info = info['entries'][0]
                url = info['url']
                title = info['title']
                self.queue.append((url, title))
                await ctx.send(f'Added to queue: {title}')
        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)

    async def play_next(self, ctx):
        try: 
            if self.queue:
                url, title = self.queue.pop(0)
                source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
                ctx.voice_client.play(source, after=lambda _: self.client.loop.create_task(self.play_next(ctx)))
                await ctx.send(f'Now playing: {title}')
            elif not ctx.voice_client.is_playing():
                await ctx.send("Queue is empty!")
        except Exception as e:
            print(e)

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("Skipped ⏭")

client = commands.Bot(command_prefix="!", intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}!')

@client.event
async def on_disconnect():
    print('Bot disconnected.')

@client.event
async def on_error(event, *args, **kwargs):
    print('Error occurred.')

async def main():
    await client.add_cog(MusicBot(client))
    await client.start("") 

asyncio.run(main())