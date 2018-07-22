import discord
from discord.ext import commands

import random


class Games:

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='roll', help='Rolls a random number (range can be specified)')
    async def roll(self, ctx, *args):
        start = 1
        stop = 100
        if not args:
            pass
        elif len(args) == 1:
            stop = args[0]
        elif len(args) == 2:
            start = args[0]
            stop = args[1]
        else:
            pass

        # Check if number, default to 0-100 if NaN
        try:
            start, stop = map(int, [start, stop])
        except:
            start = 0
            stop = 100

        await ctx.send('{} rolled {} _({}-{})_'.format(
            ctx.message.author.mention,
            random.randrange(start, stop),
            start,
            stop
        ))


def setup(bot):
    bot.add_cog(Games(bot))
