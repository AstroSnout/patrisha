from discord.ext.commands.cooldowns import BucketType
from discord.ext import commands
from helpers.db_manager import DBManager
import random


class Economy:

    def __init__(self, bot):
        self.bot = bot
        self.dbm = DBManager()

    @commands.group(name='eco', invoke_without_command=True,
                    help='Command subcategory related to economy commands')
    async def eco(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid Economy subcommand passed...\nTry using `!help eco`')

    @eco.command(name='register', aliases=['reg', 'r'], help='Register yourself in the bank!')
    async def eco_register(self, ctx):
        print(f'{ctx.message.author} requested to register in the bank')
        default_balance = 500
        status = await self.dbm.eco_register(ctx.message.author.id, default_balance)
        if status is True:
            await ctx.send('Successfully registered! Your current balance is **{}PPD**'.format(default_balance))
        else:
            await ctx.send('You are already registered.')

    @eco.command(name='balance', aliases=['b', 'bal'], help='When you want to check how much PPD you have.')
    async def eco_balance(self, ctx):
        print(f'{ctx.message.author} requested to view their balance')
        user_balance = await self.dbm.eco_view_balance(ctx.message.author.id)
        if user_balance is None:
            await ctx.send('You are not registered in the bank. Try using `!eco register` to do so!')
        else:
            await ctx.send('Your current balance is **{}PPD**'.format(user_balance))

    @eco.command(name='work', aliases=['w'], help='Work once a day to earn PPD the honest, hardworking way.')
    @commands.cooldown(rate=1, per=86400, type=BucketType.user)
    async def eco_work(self, ctx):
        print(f'{ctx.message.author} requested to work')
        earned = random.randrange(50, 150)
        status = await self.dbm.eco_add_balance(ctx.message.author.id, earned)
        if status is True:
            await ctx.send('A hard day\'s work has earned you **{}PPD**'.format(earned))
        else:
            await ctx.send('You are not registered in the bank. Try using `!eco register` to do so!')
            self.eco_work.reset_cooldown(ctx)


def setup(bot):
    bot.add_cog(Economy(bot))
