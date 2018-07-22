from discord.ext import commands


class Misc:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='invitelink', help='Gives you an invite link so you can invite Patrisha to your own server :)')
    async def invite_link(self, ctx):
        await ctx.send(f'https://discordapp.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot')


def setup(bot):
    bot.add_cog(Misc(bot))