from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType


class Misc:
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
        await self.bot.get_user(217294231125884929).send(f'User {ctx.message.author} sent feedback:\n```{feedback}```')


def setup(bot):
    bot.add_cog(Misc(bot))