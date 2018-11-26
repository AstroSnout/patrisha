from discord.ext.commands.cooldowns import BucketType
from discord.ext import commands
from helpers.db_manager import DBManager
import discord
import helpers.util as u
import random


class ATB:

    def __init__(self, bot):
        self.bot = bot
        self.dbm = DBManager()

    @commands.command(name='atb')
    async def atb_feedback(self, ctx, *, message):
        if ctx.guild is not None:
            return
        try:
            guild = self.bot.get_guild(198869638568869888)
        except:
            ctx.send('Can\'t find Albino Toilet Boys server :(')
            return

        try:
            officer_channel = self.bot.get_channel(502274247788462082)
        except:
            ctx.send('Can\'t find the officer channel :(')
            return

        try:
            member = guild.get_member(ctx.author.id)
            player_name = member.nick if member.nick is not None else member.name
            player_role = member.top_role
        except:
            player_name = ctx.author.name
            player_role = 'N/A'

        await officer_channel.send(f'Igrač {player_name} (Role: {player_role}) je napisao:\n```{message}```')
        await ctx.send('The officers successfully received your message.')


def setup(bot):
    bot.add_cog(ATB(bot))
