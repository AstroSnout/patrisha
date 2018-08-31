import discord
from discord.ext import commands
from helpers import util


class Stats:
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name='stats', alliases=['s'], invoke_without_command=True, help='Various statistics-oriented commands')
    async def stats(self, ctx):
        if ctx.invoked_subcommand is None:
            raise Exception

    @stats.command(name='post', help="Get the best post (according to total number of reacts received)")
    async def stats_post(self, ctx, limit=400):
        print(f'{ctx.message.author} requested the most popular post in the last {limit} messages')
        # Makes a list of {message:Message, reacts:int} dicts from channel history
        messages=[{'message': message, 'reacts': sum(react.count for react in message.reactions)} async for message in ctx.channel.history(limit=limit)]
        # Sorts the list in descending order
        sorted_mess = sorted(messages, key=lambda k: k['reacts'], reverse=True)
        # Get the top rated post
        top_msg, reacts = sorted_mess.pop(0).values()
        try:
            name = top_msg.author.nick
        except:
            name = top_msg.author.name
        # Print out the result (with attachments if present)
        if top_msg.attachments:

            await ctx.send('User {} has the most popular post: {} {} with {} reacts'.format(
                name,
                top_msg.content,
                top_msg.attachments[0].url,
                reacts)
            )
        else:
            await ctx.send('User {} has the most popular post: {} with {} reacts'.format(
                name,
                top_msg.content,
                reacts)
            )

    @stats.command(name='poster', help='Get the best poster (according to total number of reacts received)')
    async def stats_poster(self, ctx, limit=400):
        print(f'{ctx.message.author} requested the most popular poster in the last {limit} messages')
        # Makes a list of {message:Message, reacts:int} dicts from channel history
        messages = [{'message': message, 'reacts': sum(react.count for react in message.reactions)} async for message in ctx.channel.history(limit=limit)]
        # Get total reacts for every user that posted in the channel
        users = {}
        for d in messages:
            try:
                users[d['message'].author] += d['reacts']
            except KeyError:
                users[d['message'].author] = d['reacts']
        # Sort the users according to total reacts
        users = sorted(users.items(), key=lambda kv: kv[1], reverse=True)
        # Making of the Embed that's being sent
        embed = discord.Embed(
            title='Top posters in this channel',
            description='According to total number of reacts',
            color=util.color_pick(1100)
        )
        for i in range(5):
            try:
                author, total_reacts = users[i]
            except IndexError:
                continue
            try:
                name = author.nick
            except:
                name = author.name
            embed.add_field(
                name=f'#{name} ',
                value=f'With a total of {total_reacts} reacts',
                inline=False
            )
        # Send the result
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Stats(bot))
