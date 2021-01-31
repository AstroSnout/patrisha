from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='invitelink', aliases=['inv', 'il'], help='Gives you an invite link so you can invite Patrisha to your own server :)')
    async def invite_link(self, ctx):
        print(f'{ctx.message.author} requested an invite link')
        await ctx.send(f'https://discordapp.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot')

    @commands.command(name='feedback', aliases=['suggestion', 'suggest', 'f'], help='Any suggestions and feedback go here')
    @commands.cooldown(rate=1, per=300, type=BucketType.user)
    async def feedback(self, ctx, *, feedback):
        print(f'{ctx.message.author} has sent us some feedback')
        feedback_channel = self.bot.get_channel(805436184330895383)
        await feedback_channel.send(
            f'User {ctx.message.author.mention} sent feedback:\n```{feedback}```'
        )


def setup(bot):
    bot.add_cog(Misc(bot))
