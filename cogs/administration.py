import discord
import datetime

from discord.ext import commands
from helpers import util as u
from helpers.db_manager import DBManager


class Administration:
    def __init__(self, bot):
        self.bot = bot
        self.dbm = DBManager()

    async def _delete_messages(self, ctx, messages):
        if len(messages) > 100:
            async with ctx.typing():
                total = len(messages)
                messages = [messages[x:x + 100] for x in range(0, len(messages), 100)]

                for sublist in messages:
                    try:
                        await ctx.channel.delete_messages(sublist)
                    except discord.HTTPException:
                        my_msg = await ctx.send('Messages older than 14 days, will take a while')
                        count = 1
                        for list in messages:
                            for msg in list:
                                await msg.delete()
                                await my_msg.edit(content='Messages older than 14 days, will take a while'
                                                          '\nDeleting {} out of {} messages'.format(count, total))
                                count += 1
        else:
            async with ctx.typing():
                await ctx.channel.delete_messages(messages)
                total = len(messages)

        return total

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.command(name='on_join')
    async def on_join_message(self, ctx, *, message):
        await self.dbm.modify_on_join_message(message, ctx.channel.guild)
        await ctx.send('Updated this guild\'s on join message!')

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.command(name='default_role')
    async def on_join_role(self, ctx, *, role_name):
        status = await self.dbm.modify_on_join_role(role_name, ctx.channel.guild)
        print(role_name)
        if status:  # Success
            await ctx.send('Updated this guild\'s on join role!')
        else:  # Failed
            await ctx.send('Role was not found :(')

    @commands.guild_only()
    @commands.group(name='a', invoke_without_command=True, help='Server moderation and administration related commands')
    async def a(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.bot.get_command('help'), 'a')

    @commands.is_owner()
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    @a.command(name='prune', aliases=['p', 'delete', 'del'], help='Delete # of messages specified in invoked channel')
    async def prune(self, ctx, *args):
        print(args)
        # Check if admin
        # Default = Delete a number of messages specified
        # If -u {user.mention} or --user {user.mention} = delete a number of messages specified made by specified user
        # If mins={number of minutes} = deletes all messages going back specified amount of minutes
        # Don't forget to print out them sexy stats
        # Call a different function based on kwargs

        try:
            amount = int(args[0]) + 1  # added one since we're ignoring the invocation
        except ValueError:
            await ctx.invoke(self.bot.get_command('help'), 'a', 'p')
            return

        # Check if user provided in there
        # Either one or the other, but not both
        user = None
        if '-u' in args:
            try:
                user = args[args.index('-u') + 1]  # next argument should be the user
            except:
                await ctx.invoke(self.bot.get_command('help'), 'a', 'p')
                return
        elif '--user' in args:
            try:
                user = args[args.index('--user') + 1]  # next argument should be the user
            except:
                await ctx.invoke(self.bot.get_command('help'), 'a', 'p')
                return

        if user:
            if user.startswith('<@!'):  # Invoker mentioned user whose messages they want deleted
                user = int(user.replace('<@!', '').replace('>', ''))
            else:
                user = user.lower()

        print('user =', user)
        # Check if modifiers (-m or --minutes) are present
        if '-m' in args or '--minutes' in args:
            since_when_to_delete = datetime.datetime.utcnow() - datetime.timedelta(minutes=amount)  # This is fine
            messages = [
                msg async for msg in ctx.channel.history(after=since_when_to_delete, reverse=True)
                if msg.author.id == user or msg.author.name.lower() == user or user is None
            ]
        # No -m modifier
        else:
            messages = [
                msg async for msg in ctx.channel.history(limit=amount, reverse=True)
                if msg.author.id == user or msg.author.name.lower() == user or user is None
            ]

            # async for msg in ctx.channel.history(limit=amount, reverse=True):
            #     if msg.author.id == user or msg.author.nick.lower() == user or user is None:
            #         print(msg)

        if user is None or ctx.message.author.id == user or ctx.message.author.nick == user:
            messages.pop(-1)
        total = await self._delete_messages(ctx, messages)

        stats = discord.Embed(
            title=' ',
            description=' ',
            color=u.color_pick(5000)
        ).set_author(
            name='Pruned messages stats'
        ).add_field(
            name='Removed',
            value='```{} messages```'.format(total),
            inline=False
        )

        await ctx.send(embed=stats)


def setup(bot):
    bot.add_cog(Administration(bot))
