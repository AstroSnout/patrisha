import asyncio

import discord
import os
import threading
import math

from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from helpers import util as u
from helpers.ytdl import YTDLSource, YTDLDownloader, Song

class Music(commands.Cog):
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
            return await YTDLSource.get_playable_song(song.url, loop=self.bot.loop)

    # Tries to download the next song
    async def _download_next(self, song: Song):
        try:
            next_song = self.song_queue[song.sid][1]
            print(next_song.title)
            if not os.path.exists(f'{next_song.filename}'):
                threading.Thread(target=YTDLDownloader.client.download, args=(next_song.title,), daemon=True).start()
                print(f'Downloaded {next_song.title}')
        except IndexError:
            pass

    # Clears the song queue
    async def _clear_que(self, sid):
        self.song_queue[sid] = []

    # Notifies users that it finished playing and leaves voice channel
    async def _finished_playing(self, guild_id, channel_id):
        self.now_playing = None
        channel = self.bot.get_channel(channel_id)
        guild = self.bot.get_guild(guild_id)
        await self._clear_que(guild_id)
        await channel.send(f':x: Finished playing - Leaving **__{guild.voice_client.channel.name}__** channel!')
        await guild.voice_client.disconnect()

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
        guild = self.bot.get_guild(song.sid)
        channel = self.bot.get_channel(song.channel_id)

        # Define the callback for when the player finishes playing
        def my_after(error):
            if error:
                print('Error in \'Music._play_song\':', error)
            # Play next if queue isn't empty
            if queue:
                now_playing = queue.pop(0)
                coro = self._play_song(now_playing)
                future = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
                self.now_playing = now_playing
                try:
                    future.result()
                except:
                    pass
            # Notify user and disconnect otherwise
            else:
                coro = self._finished_playing(song.sid, song.channel_id)
                future = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
                try:
                    future.result()
                except:
                    pass

        # Notify the user and play the song
        if not guild.voice_client.is_playing():
            await channel.send(embed=await song.make_embed_playing(self.song_queue[song.sid]))
            guild.voice_client.play(player, after=my_after)

    @commands.cooldown(rate=1, per=3, type=BucketType.user)
    @commands.command(name='play', aliases=['p', 'stream'], help='Plays a song from YouTube - You can use URLs or song names (picks the first result)')
    async def play(self, ctx, *, url):
        # @play.before_invoke functions below - ensure_voice()
        msg = await ctx.send(f'{u.get_emoji("youtube")}:mag_right: Searching...')
        # Bot is not connected to voice (probably redundant due to ensure_voice func below)
        if not ctx.voice_client:
            await ctx.send(f'Bot is not connected to a channel :(')

        async with ctx.typing():
            data = await YTDLSource.song_name(url, loop=self.bot.loop)
            song = Song(
                ctx.message.guild.id,
                ctx.message.author,
                ctx.message.channel.id,
                filename=YTDLDownloader.client.prepare_filename(data),
                title=data['title'],
                url=data['webpage_url'],
                uploader=data['uploader'],
                thumbnail=data['thumbnail'],
                duration=data['duration'],
                views=data['view_count']
            )

            if not ctx.voice_client.is_playing():
                self.now_playing = song
                await self._play_song(song)
                await msg.delete()
            else:
                # Download if not available locally
                if not os.path.exists(f'{song.filename}'):
                    threading.Thread(target=YTDLDownloader.client.download, args=(url,)).start()
                    print(f'Downloaded {song.title}')
                # Add to que
                self.song_queue[ctx.message.guild.id].append(song)  # Tries to append
                # Inform the invoker
                await msg.delete()
                queue_len = len(self.song_queue[ctx.message.guild.id])
                await ctx.send(embed=await song.make_embed_queued(queue_len))

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
