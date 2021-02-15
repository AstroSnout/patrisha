import discord
import asyncio
import youtube_dl
import datetime

class YTDLDownloader:
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
        'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
    }

    ffmpeg_options = {
        'before_options': '-nostdin',
        'options': '-vn'
    }

    client = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):

    def __init__(self, source, *, data, volume=1):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def get_playable_song(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: YTDLDownloader.client.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else YTDLDownloader.client.prepare_filename(data)
        return cls(
            discord.FFmpegPCMAudio(
                filename, **YTDLDownloader.ffmpeg_options
            ), data=data)

    @classmethod
    async def song_name(cls, search, loop=None):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: YTDLDownloader.client.extract_info(search, download=False))
        try:
            data = data['entries'][0]
        except KeyError:
            # It's the only result
            pass
        except TypeError:
            pass

        return data


class Song:
    def __init__(self, sid, owner, channel_id, filename=None, title=None, url=None, uploader=None, thumbnail=None, duration=None, views=None):
        self.sid = sid
        self.owner = owner  # ctx.message.author
        self.channel_id = channel_id
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

    async def make_embed_queued(self, queue_len):
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
            value=f'It is currently #{queue_len}'
        )
        embed.set_footer(
            text=f'Requested by: {self.owner.nick}'
        )
        embed.timestamp = datetime.datetime.utcnow()
        return embed
