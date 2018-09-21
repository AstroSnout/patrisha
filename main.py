import discord
from discord.ext import commands

import sys
import traceback
import asyncio
import time
import datetime
import youtube_dl

from helpers import cfg, bg_tasks, misc
from helpers.db_manager import DBManager

"""This is a multi file example showcasing many features of the command extension and the use of cogs.
These are examples only and are not intended to be used as a fully functioning bot. Rather they should give you a basic
understanding and platform for creating your own bot.
These examples make use of Python 3.6.2 and the rewrite version on the lib.
For examples on cogs for the async version:
https://gist.github.com/leovoel/46cd89ed6a8f41fd09c5
Rewrite Documentation:
http://discordpy.readthedocs.io/en/rewrite/api.html
Rewrite Commands Documentation:
http://discordpy.readthedocs.io/en/rewrite/ext/commands/api.html
Familiarising yourself with the documentation will greatly help you in creating your bot and using cogs.
"""
# Bot wants ManageMessages, ReadChannelHistory


def get_prefix(bot, message):
    prefixes = ['!']
    if not message.guild:
        return '!'
    return commands.when_mentioned_or(*prefixes)(bot, message)


# Below cogs represents our folder our cogs are in. Following is the file name. So 'meme.py' in cogs, would be cogs.meme
# Think of it like a dot path import
initial_extensions = ['cogs.game_wow',
                      'cogs.games',
                      'cogs.economy',
                      'cogs.gamble',
                      'cogs.music',
                      'cogs.stats',
                      'cogs.misc',
                      'cogs.administration',
                      ]

# BG Task list function
bg_task_list = [
    bg_tasks.guild_sub_sending
]

bot_version = '2.4.2'
bot = commands.Bot(command_prefix=get_prefix, description='Patrisha', formatter=misc.Helper())
dbm = DBManager()
me = None

async def background_tasks():
    await bot.wait_until_ready()
    print('The bot is now ready!')
    print('---------------------')
    while not bot.is_closed():
        for task in bg_task_list:
            await task(bot)
            print(f'Executed BG task: {task.__name__}')
            # await me.send(f'```<{datetime.datetime.now()}> Executed BG task: {task.__name__}```')
        await asyncio.sleep(1200)  # task runs every 1200 seconds

# Here we load our extensions(cogs) listed above in [initial_extensions].
if __name__ == '__main__':
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print(f'Failed to load extension {extension}.', file=sys.stderr)
            traceback.print_exc()


@bot.event
async def on_ready():
    global me
    await bot.change_presence(activity=discord.Game(name='try using !help'))
    await bot.user.edit(username=f'Patrisha')
    me = bot.get_user(217294231125884929)

    print(f'Logged in as: {bot.user.name} - {bot.user.id}')
    print(f'Version: {bot_version}')
    print('---------------------')

    for guild in bot.guilds:
        await dbm.create_settings_if_none(guild)
        # await guild.get_member(bot.user.id).edit(nick=f'Patrisha')
        print('>> - Present in', guild)
    print('---------------------')
    print(f'Successfully logged in and booted...!')
    print('---------------------')


@bot.event
async def on_message(message):
    await bot.process_commands(message)


@bot.event
async def on_guild_join(guild):
    await dbm.create_settings_if_none(guild)


@bot.event
async def on_member_join(member):
    server_message = await dbm.get_server_message(member.guild)
    await member.send(server_message)

    member_role = await dbm.get_server_role(member.guild)
    for role in member.guild.roles:
        if member_role.lower() == role.name.lower():
            await member.add_roles(role, reason='Default role by PatrishaBot')

    await me.send(
        f'''
        User {member.name} has joined {member.guild.name}
        Default role: `{member_role}`
        Default message: ```{server_message}```
        '''
    )


@bot.event
async def on_command_error(ctx, error):
    print(ctx, error)
    await me.send(f'{ctx.message.content} caused an error:\n{error}')  # DMs me

    if 'Signature extraction failed' in str(error):
        await ctx.send('YouTube probably pushed an update that broke something :(')
    if 'ffmpeg was not found' in str(error):
        await ctx.send(f'My magnificent creator forgot to give me ffmpeg :)')
    if isinstance(error, discord.errors.Forbidden):
        await ctx.send(f'I am missing the required permissions to do this command')
    if isinstance(error, commands.errors.CommandOnCooldown):
        # time_str = time.strftime("%H:%M:%S", time.gmtime(int(error.retry_after)))
        await ctx.send(f'You are on cooldown. Try again in {str(error.retry_after)[:4]}s')
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send(f':x: I need more information in order to do that command!\n'
                       f'Try running `!help <command name>`')


bot.loop.create_task(background_tasks())
bot.run(cfg.BOT_TOKEN, bot=True, reconnect=True)
