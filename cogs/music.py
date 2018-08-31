import asyncio

import discord
import youtube_dl
import os
import threading
import datetime

from discord.ext import commands
from helpers import util as u

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': 'dl/%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'before_options': '-nostdin',
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=1):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

    @classmethod
    async def song_name(cls, search, ctx, loop=None):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search, download=False))
        data = data['entries'][0]
        print(data)
        song = Song(
            ctx,
            filename=ytdl.prepare_filename(data),
            title=data['title'],
            url=data['webpage_url'],
            uploader=data['uploader'],
            thumbnail=data['thumbnail'],
            duration=data['duration'],
            views=data['view_count']
        )
        return song

    @classmethod
    def download(cls, url):
        ytdl.download([url])
        print('dl finish')


class Song:
    def __init__(self, ctx, filename=None, title=None, url=None, uploader=None, thumbnail=None, duration=None, views=None):
        self.ctx = ctx
        self.sid = ctx.message.guild.id
        self.filename = filename
        self.title = title
        self.url = url
        self.uploader = uploader
        self.thumbnail = thumbnail
        self.duration = str(datetime.timedelta(seconds=duration))  # Converts to min:sec
        self.views = views

        print(self.duration)


    def __str__(self):
        return str(self.title)

    def __repr__(self):
        return str(self.title)

    async def make_embed_playing(self, queue):
        embed = discord.Embed(
            title='',
            description='',
            color=u.color_pick(4300)
        )
        embed.set_thumbnail(
            url=self.thumbnail
        )
        embed.set_author(
            name=f'{self.title} ({self.duration})',
            url=self.url,
        )
        embed.add_field(
            name='Uploader',
            value=self.uploader,
            inline=True
        )
        embed.add_field(
            name='Views',
            value=self.views,
            inline=True
        )
        up_next = queue[0].title if queue else 'Looks like your queue is empty'
        embed.add_field(
            name='Coming up next:',
            value=up_next
        )
        return embed


    async def make_embed_queued(self, queue):
        embed = discord.Embed(
            title='',
            description='',
            color=u.color_pick(4300)
        )
        embed.set_thumbnail(
            url=self.thumbnail
        )
        embed.set_author(
            name=f'{self.title} ({self.duration})',
            url=self.url,
        )
        embed.add_field(
            name='Uploader',
            value=self.uploader,
            inline=True
        )
        embed.add_field(
            name='Views',
            value=self.views,
            inline=True
        )
        embed.add_field(
            name='Position in queue:',
            value=f'It is currently #{len(queue)}'
        )
        return embed



class Music:
    def __init__(self, bot):
        self.bot = bot
        self.song_queue = {}

    async def _clear_que(self, sid):
        self.song_queue[sid] = []

    async def _play_local(self, song: Song):
        if not song.ctx.voice_client.is_playing():
            print(f'Playing a local audio file in {song.ctx.channel.name}')
            player = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(song.filename))
            song.ctx.voice_client.play(
                player,
                after=lambda e:
                self.bot.loop.create_task(self._play_song(self.song_queue[song.sid].pop(0)))
                if self.song_queue
                else
                self.bot.loop.create_task(song.ctx.send('Finished playing!'))
            )

    async def _play_and_download(self, song: Song):
        if not song.ctx.voice_client.is_playing():
            # Downloader didn't download in time :(
            player = await YTDLSource.from_url(song.url, loop=self.bot.loop)
            song.ctx.voice_client.play(
                player,
                after=lambda e:
                self.bot.loop.create_task(self._play_song(self.song_queue[song.sid].pop(0)))
                if self.song_queue
                else
                self.bot.loop.create_task(song.ctx.send('Finished playing!'))
            )

    async def _play_song(self, song: Song):
        if os.path.exists(f'{song.filename}'):
            await self._play_local(song)
        else:
            async with song.ctx.typing():
                await self._play_and_download(song)

        await song.ctx.send(f'Now playing: **__{song.title}__** :musical_note: ',
                            embed=await song.make_embed_playing(self.song_queue[song.sid]))

    @commands.command(name='play', aliases=['p', 'stream'],help='Plays a song from YouTube - You can use URLs or song names (picks the first result)')
    async def play(self, ctx, *, url):
        if ctx.voice_client:
            url = url.replace(':', '')  # semi-colon breaks this for whatever reason
            # Get filename and song title
            async with ctx.typing():
                song = await YTDLSource.song_name(url, ctx, loop=self.bot.loop)
                try:
                    self.song_queue[song.sid]
                except KeyError:
                    self.song_queue[song.sid] = []
            # Play ASAP if not playing (avoids the request below, saving time)
            if not ctx.voice_client.is_playing():
                await self._play_song(song)
            # The bot is actually playing
            else:
                # Download if not available locally
                if not os.path.exists(f'{song.filename}'):
                    threading.Thread(target=YTDLSource.download, args=(url, )).start()
                    print('done with dl')
                # Add to que
                try:
                    self.song_queue[song.sid].append(song)  # Tries to append
                except KeyError:
                    self.song_queue[song.sid] = [song]  # Means this server isn't in the dict
                # Inform the invoker
                await ctx.send(f'Your song has been queued\n',
                               embed=await song.make_embed_queued(self.song_queue[song.sid]))

    @commands.command(name='stop', aliases=['disconnect', 'dc'], help='Stops the music and disconnects the bot from the voice channel')
    async def stop(self, ctx):
        await ctx.send(f"Stopped music and disconnected from - **__{ctx.author.voice.channel.name}__**.")
        await self._clear_que(ctx.message.guild.id)
        await ctx.voice_client.disconnect()

    @commands.command(name='skip', help='Skips the current song and plays the next one in queue')
    async def skip(self, ctx):
        if ctx.voice_client is None:
            await ctx.send(":x: I'm not connected to a voice channel.")
            return
        sid = ctx.message.guild.id
        if self.song_queue[sid]:
            ctx.voice_client.stop()
        else:
            await ctx.send('No more songs in queue!')

    @commands.command(name='queue', aliases=['que'], help='Shows the current song queue')
    async def queue(self, ctx):
        sid = ctx.message.guild.id
        try:
            self.song_queue[sid]
        except KeyError:
            await ctx.send('No songs in queue!')
            return

        if ctx.voice_client:
            songs = "\n".join('{}. {}'.format(i+1, str(self.song_queue[sid][i])) for i in range(len(self.song_queue[sid])))
            await ctx.send('Songs currently in queue:```{0}```'.format(songs))
        else:
            await ctx.send(":x: I am not connected to a voice channel.")

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.send(f":white_check_mark: Connected to voice channel - **__{ctx.author.voice.channel.name}__**.")
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send(":x: You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        # elif ctx.voice_client.is_playing():
        #     ctx.voice_client.stop()


def setup(bot):
    bot.add_cog(Music(bot))