import asyncio

import discord
import youtube_dl
import os
import threading
import datetime
import bs4
import requests
import math

from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from helpers import util as u

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'worstaudio/worst',
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
        try:
            data = data['entries'][0]
        except KeyError:
            # It's the only result
            pass
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
    def get_playlist_links(cls, user_link):
        # Meme one-liner
        # So, this gets the page, finds all <a> elements
        # then find hrefs in those elements and then within those
        # hrefs, filters out the /watch ones (duplicates handled with set())
        # and once that's done, appends 'youtube.com' to the result and
        # removes everything after the '&' in watch link
        return set(['youtube.com' + href.split('&')[0] for link in
                    bs4.BeautifulSoup(requests.get(user_link).content, 'html.parser').find_all('a') for href in
                    link.get('href').split('\n') if 'watch' in href])

    @classmethod
    def download(cls, url):
        ytdl.download([url])


class Song:
    def __init__(self, ctx, filename=None, title=None, url=None, uploader=None, thumbnail=None, duration=None, views=None):
        self.ctx = ctx
        self.sid = ctx.message.guild.id
        self.owner = ctx.message.author
        self.filename = filename
        self.title = title
        self.url = url
        self.uploader = uploader
        self.thumbnail = thumbnail
        self.duration = str(datetime.timedelta(seconds=duration))  # Converts to min:sec
        self.views = views

    def __str__(self):
        return str(self.title)

    def __repr__(self):
        return str(self.title)

    async def make_embed_playing(self, queue):
        embed = discord.Embed(
            title='',
            description='',
            color=0x33cc33
        )
        embed.set_image(
            url=self.thumbnail
        )
        embed.set_author(
            name=f'Now Playing: {self.title} ({self.duration})',
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

        embed.set_footer(
            text=f'Requested by: {self.owner.nick}'
        )
        embed.timestamp = datetime.datetime.utcnow()
        return embed

    async def make_embed_queued(self, queue):
        embed = discord.Embed(
            title='',
            description='',
            color=0xe6e600
        )
        embed.set_thumbnail(
            url=self.thumbnail
        )
        embed.set_author(
            name=f'Queued - {self.title} ({self.duration})',
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
        embed.set_footer(
            text=f'Requested by: {self.owner.nick}'
        )
        embed.timestamp = datetime.datetime.utcnow()
        return embed


class Music:
    def __init__(self, bot):
        self.bot = bot
        self.song_queue = {}
        self.now_playing = None
        self.skip_counter = 0
        self.skip_voters = []

    # Returns a discord.PCMVolumeTransformer object to play
    async def _get_player(self, song: Song):
        if os.path.exists(f'{song.filename}'):
            return discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(song.filename))
        else:
            async with song.ctx.typing():
                return await YTDLSource.from_url(song.url, loop=self.bot.loop)

    # Tries to download the next song
    async def _download_next(self, song: Song):
        try:
            next_song = self.song_queue[song.sid][1]
            print(next_song.title)
            if not os.path.exists(f'{next_song.filename}'):
                threading.Thread(target=YTDLSource.download, args=(next_song.title,)).start()
                print(f'Downloaded {next_song.title}')
        except IndexError:
            pass

    # Clears the song queue
    async def _clear_que(self, sid):
        self.song_queue[sid] = []

    # Notifies users that it finished playing and leaves voice channel
    async def _finished_playing(self, ctx):
        self.now_playing = None
        self._clear_que(ctx.guild.id)
        await ctx.send(f':x: Finished playing, leaving **__{ctx.author.voice.channel.name}__**!')
        await ctx.voice_client.disconnect()

    # Plays a song (local+downloaded)
    async def _play_song(self, song: Song):
        # Reset the counter to 0
        self.skip_counter = 0
        # Tries to download the next song in queue
        await self._download_next(song)
        # Get the player (Local or download the song)
        player = await self._get_player(song)
        # Make the queue more readable
        queue = self.song_queue[song.sid]

        # Define the callback for when the player finishes playing
        def after(error):
            if error:
                print('Error in \'Music._play_song\':', error)
            # Play next if queue isn't empty
            if queue:
                now_playing = queue.pop(0)
                self.bot.loop.create_task(
                    self._play_song(now_playing)
                )
                self.now_playing = now_playing
            # Notify user and disconnect otherwise
            else:
                self.bot.loop.create_task(
                    self._finished_playing(song.ctx)
                )

        # Notify the user and play the song
        if not song.ctx.voice_client.is_playing():
            await song.ctx.send(embed=await song.make_embed_playing(self.song_queue[song.sid]))
            song.ctx.voice_client.play(player, after=after)

    @commands.cooldown(rate=1, per=3, type=BucketType.user)
    @commands.command(name='play', aliases=['p', 'stream'],help='Plays a song from YouTube - You can use URLs or song names (picks the first result)')
    async def play(self, ctx, *, url):
        # @play.before_invoke functions below - ensure_voice()
        playlist = False
        msg = await ctx.send(f'{u.get_emoji("youtube")}:mag_right: Searching...')
        '''------------- String formatting the input -------------'''
        # Check if it's a playlist
        if 'playlist?list=' in url:
            all_songs = [song for song in YTDLSource.get_playlist_links(url)]
            playlist = True
        # Check if it's a link
        elif 'https://' in url:
            # Check if shorthand
            if 'youtu.be' in url:
                url = url.split('youtu.be/')[1]
                print('youtu.be id - ', url)
            # This should be the full link
            else:
                temp = url.split('&')[0]
                url = temp.replace('https://www.youtube.com/watch?v=', '')
                print(url)

        # Bot is connected (probably redundant due to ensure_voice func below)
        if ctx.voice_client:
            url = url.replace(':', '')  # semi-colon breaks this for whatever reason
            # Get filename and song title
            if playlist:
                async with ctx.typing():
                    for playlist_song in all_songs:
                        # Get all the song metadata
                        song = await YTDLSource.song_name(playlist_song, ctx, loop=self.bot.loop)
                        # Add the song to the que instantly
                        self.song_queue[song.sid].append(song)
                        if len(self.song_queue[song.sid]) < 2:
                            for song in self.song_queue[song.sid]:
                                if not os.path.exists(f'{song.filename}'):
                                    threading.Thread(target=YTDLSource.download, args=(song.title,)).start()
                                    print(f'Downloaded {song.title}')
                        # Play if nothing is playing while we do stuff in the background
                        if not ctx.voice_client.is_playing() and playlist_song == all_songs[0]:
                            self.now_playing = song
                            await self._play_song(
                                self.song_queue[song.sid].pop(0)
                            )
                            await msg.delete()
                    await ctx.send(f'Your playlist has been queued\n')
            else:
                async with ctx.typing():
                    song = await YTDLSource.song_name(url, ctx, loop=self.bot.loop)

                    if not ctx.voice_client.is_playing():
                        self.now_playing = song
                        await self._play_song(song)
                        await msg.delete()
                    else:
                        # Download if not available locally
                        if not os.path.exists(f'{song.filename}'):
                            threading.Thread(target=YTDLSource.download, args=(url,)).start()
                            print(f'Downloaded {song.title}')
                        # Add to que
                        self.song_queue[song.sid].append(song)  # Tries to append
                        # Inform the invoker
                        await msg.delete()
                        await ctx.send(embed=await song.make_embed_queued(self.song_queue[song.sid]))

    @commands.cooldown(rate=1, per=3, type=BucketType.user)
    @commands.command(name='stop', aliases=['disconnect', 'dc'], help='Stops the music and disconnects the bot from the voice channel')
    async def stop(self, ctx):
        self.now_playing = None
        await ctx.send(f"Stopped music and disconnected from - **__{ctx.author.voice.channel.name}__**.")
        await self._clear_que(ctx.guild.id)
        await ctx.voice_client.disconnect()

    @commands.cooldown(rate=1, per=3, type=BucketType.user)
    @commands.command(name='skip', help='Skips the current song and plays the next one in queue')
    async def skip(self, ctx):
        if ctx.voice_client is None:
            await ctx.send(":x: I'm not connected to a voice channel.")
            return

        author = ctx.message.author
        owner = self.now_playing.owner

        if author.id == owner.id:
            await ctx.send(':fast_forward: Skipping (requested by song requester)')
            ctx.voice_client.stop()
        else:
            if self.skip_counter == 0:
                ctx.send(f':confetti_ball: {author.mention} has started a vote skip! :confetti_ball:')
            voice_members = [member for member in ctx.voice_client.channel.members if member != self.bot.user]
            required_skips = math.ceil(len(voice_members)/2)
            if author.id not in self.skip_voters:
                self.skip_counter += 1
                self.skip_voters.append(author.id)
            else:
                await ctx.send(f'{author.mention} already voted!')

            if self.skip_counter >= required_skips:
                await ctx.send(':fast_forward: Skipping (enough votes reached)')
                ctx.voice_client.stop()
            else:
                await ctx.send(f'Required votes - **{self.skip_counter}/{required_skips}**')

    @commands.command(name='queue', aliases=['que'], help='Shows the current song queue')
    async def queue(self, ctx):
        sid = ctx.message.guild.id
        if ctx.voice_client:
            songs = "\n".join('{}. {}'.format(i+1, str(self.song_queue[sid][i])) for i in range(len(self.song_queue[sid])))
            if len(songs) > 2000:
                songs = songs[:1900] + '...'

            if songs:
                await ctx.send('Songs currently in queue:```{0}```'.format(songs))
            else:
                await ctx.send('No songs in queue :/')
        else:
            await ctx.send(":x: I am not connected to a voice channel.")

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.send(f":white_check_mark: Connected to voice channel - **__{ctx.author.voice.channel.name}__**.")
                await ctx.author.voice.channel.connect()
                # Initialize a queue
                try:
                    self.song_queue[ctx.guild.id]
                except KeyError:
                    self.song_queue[ctx.guild.id] = []
                self.skip_counter = 0
            else:
                await ctx.send(":x: You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")

        print('Ensured voice')



def setup(bot):
    bot.add_cog(Music(bot))