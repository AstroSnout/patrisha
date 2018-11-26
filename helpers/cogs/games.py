import discord
from discord.ext import commands

import random


class Games:

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='roll', help='Rolls a random number (range can be specified)')
    async def roll(self, ctx, *args):
        print(f'{ctx.message.author} requested a random roll with arguments {args}')
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

    @commands.command(name='droll', help='Roll a die in {number of dies}d{sides on the die} (3d6 for example would roll a 6-sided die 3 times)')
    async def droll(self, ctx, *, args):
        try:
            number_of_dies, die_size = args.split('d')
            number_of_dies = int(number_of_dies)
            die_size = int(die_size)
        except:
            await ctx.send('Invalid arguments passed')
            return

        steps = []
        for i in range(number_of_dies):
            roll = random.randrange(1, die_size+1)
            steps.append(str(roll))

        total = sum([int(x) for x in steps])

        await ctx.send('You rolled {}d{}:\n{}={}'.format(
            number_of_dies,
            die_size,
            '+'.join(steps),
            total
        ))


def setup(bot):
    bot.add_cog(Games(bot))
