import discord
from discord.ext import commands

import sys
import traceback
import datetime
# import cogs
import configparser

from helpers import misc
from helpers.db_manager import DBManager


class Patrisha(discord.ext.commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings = configparser.ConfigParser()
        self.settings.read('settings.ini')

        # self.bg_task_list = [
        #     bg_tasks.guild_sub_sending,
        #     bg_tasks.new_atb_apps
        # ]

        # self.bg_task = self.loop.create_task(
        #     self.bg_tasks()
        # )

        self.version = self.settings['meta']['version']
        self.dbm = DBManager(
            self.settings['database']['username'],
            self.settings['database']['password'],
            self.settings['database']['dbname'],
        )
        db = self.dbm.client.test
        print(db)

    async def on_ready(self):
        await self.change_presence(activity=discord.Game(name='Evolving \o/'))

        print(f'Logged in as: {self.user.name} - {self.user.id}')
        print(f'Version: {self.version}')
        print('---------------------')

        for guild in self.guilds:
            await self.dbm.init_settings(guild)

        print('---------------------')
        print(f'Successfully logged in and booted in {len(self.guilds)} servers...!')
        print('---------------------')
    
    async def on_message(self, message):
        await self.process_commands(message)


    # async def on_guild_join(self, guild):
    #     await self.dbm.init_settings(guild)


    # async def on_member_join(self, member):
    #     server_message = await self.dbm.get_on_join_message(member.guild)
    #     await member.send(server_message)
    #
    #     member_role = await self.dbm.get_on_join_role(member.guild)
    #     for role in member.guild.roles:
    #         if member_role.lower() == role.name.lower():
    #             await member.add_roles(role, reason='Default role by PatrishaBot')


    async def on_command_error(self, ctx, error):
        print(ctx, error)
        error_channel = self.get_channel(805435706196623401)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        await error_channel.send(
            f'[{datetime.datetime.now():%H:%M:%S}] User {ctx.author.name} sent `{ctx.message.content}` that caused an error:'
            f'\n```{error}```'
        )
    
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

    # async def bg_tasks(self):
    #     try:
    #         await self.wait_until_ready()
    #
    #         bg_tasks_channel = self.get_channel(504697387927732234)
    #
    #         print('The bot is now ready!')
    #         print('---------------------')
    #         while not self.is_closed():
    #             for task in self.bg_task_list:
    #                 await task(self)
    #                 print(f'Executed BG task: {task.__name__}')
    #                 await bg_tasks_channel.send(f'```[{datetime.datetime.now():%H:%M:%S}] Executed BG task: {task.__name__}```')
    #             await asyncio.sleep(120)  # task runs every 1200 seconds
    #     except Exception as e:
    #         print('Error!')
    #         print(traceback.print_exc())
    #         self.bg_task = self.loop.create_task(
    #             self.bg_tasks()
    #         )

# Bot wants ManageMessages, ReadChannelHistory
def get_prefix(bot, message):
    prefixes = ['!']
    if not message.guild:
        return '!'
    return commands.when_mentioned_or(*prefixes)(bot, message)

initial_extensions = [
    # 'cogs.games',
    # 'cogs.economy',
    # 'cogs.gamble',
    # 'cogs.stats',
    'cogs.administration',
    # 'cogs.music',
    'cogs.game_wow',
    'cogs.misc',
    # Non-generic cogs
    # 'cogs.atb',
]

bot = Patrisha(command_prefix=get_prefix, description='Patrisha', formatter=misc.Helper())

if __name__ == '__main__':
    for extension in initial_extensions:
        try:
            print(extension)
            bot.load_extension(extension)
        except Exception as e:
            print(f'Failed to load extension {extension}.', file=sys.stderr)
            traceback.print_exc()

bot.run(bot.settings['discord']['token'], bot=True, reconnect=True)
