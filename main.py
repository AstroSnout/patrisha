import discord
from discord.ext import commands

import sys
import traceback
import asyncio
import time
from helpers import cfg, bg_tasks, misc

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
                      ]

bot_version = '2.3.3'
bot = commands.Bot(command_prefix=get_prefix, description='Patrisha', formatter=misc.Helper())


async def background_tasks():
    await bot.wait_until_ready()
    print('The bot is now ready!')
    print('---------------------')
    while not bot.is_closed():
        await bg_tasks.guild_sub_sending(bot)
        print('Executed some BG tasks')
        await asyncio.sleep(600)  # task runs every 60 seconds

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
    # Changes our bots Playing Status. type=1(streaming) for a standard game you could remove type and url.
    await bot.change_presence(activity=discord.Game(name='In Development'))
    await bot.user.edit(username=f'Patrisha v{bot_version}')

    print(f'Logged in as: {bot.user.name} - {bot.user.id}')
    print(f'Version: {bot_version}')
    print('---------------------')

    for guild in bot.guilds:
        await guild.get_member(bot.user.id).edit(nick=f'Patrisha v{bot_version}')
        print('>> - Changed nick in', guild)
    print('---------------------')
    print(f'Successfully logged in and booted...!')
    print('---------------------')


@bot.event
async def on_message(message):
    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    print(ctx, error)
    await ctx.send(
        f'An error has occurred while trying to process your command:\n'
        f'```{str(error)}```\n'
        f'Try using `!help <command name>`'
    )
    if 'ffmpeg was not found' in str(error):
        await ctx.send(f'My magnificent creator forgot to give me ffmpeg :)')
    if isinstance(error, commands.errors.CommandOnCooldown):
        time_str = time.strftime("%H:%M:%S", time.gmtime(int(error.retry_after)))
        await ctx.send(f'Command on cooldown - available in {time_str}')


bot.loop.create_task(background_tasks())
bot.run(cfg.BOT_TOKEN, bot=True, reconnect=True)
