from discord.ext import commands
from helpers.db_manager import DBManager
import random

slot_help = 'The payout is equal to bet amount multiplied by the values in the pay table\n' \
            'Pay table:\n' \
            ' :apple:    :apple:   :apple: - 5000\n' \
            ' :pear:    :pear:   :pear: - 1000\n' \
            ' :lemon:    :lemon:   :lemon: - 200\n' \
            ' :peach:    :peach:   :peach: - 100\n' \
            ' :strawberry:    :strawberry:   :strawberry: - 50\n' \
            ' :grapes:   :grapes:   :grapes: - 25\n' \
            'ANY  :grapes:   :grapes: - 10\n' \
            'ANY ANY :grapes: - 2'


class Gamble:

    def __init__(self, bot):
        self.bot = bot
        self.dbm = DBManager()

    @commands.command(name='slot', help=slot_help)
    async def gamble_slot(self, ctx, amount: int):
        print(f'{ctx.message.author} requested to gamble on the slot machine for {amount} money')
        reel1_weights = [4, 5, 6, 6, 7, 8, 28]
        reel2_weights = [3, 4, 4, 5, 5, 6, 37]
        reel3_weights = [1, 2, 3, 4, 6, 6, 42]
        payouts = {':apple:': 5000,
                   ':pear:': 1000,
                   ':lemon:': 200,
                   ':peach:': 100,
                   ':strawberry:': 50,
                   ':grapes:': 25,
                   ':x:': 0}

        user_balance = await self.dbm.eco_view_balance(ctx.author.id)
        if user_balance is None:
            await ctx.send('You are not registered in the bank. Try using `!eco register` to do so!')
        elif user_balance < amount:
            await ctx.send('You do not have enough PPDs :(')
        else:
            await self.dbm.eco_rem_balance(ctx.author.id, amount)
            result = random.choices(list(payouts.keys()), weights=reel1_weights) + \
                     random.choices(list(payouts.keys()), weights=reel2_weights) + \
                     random.choices(list(payouts.keys()), weights=reel3_weights)
            # Three of a kind
            if len(set(result)) <= 1 and result[0] != ':x:':
                await self.dbm.eco_add_balance(ctx.author.id, payouts[result[0]]*amount)
                gratz = f'Three of a kind! You won {payouts[result[0]]*amount}PPD'
            elif result.count(':grapes:') == 2:
                await self.dbm.eco_add_balance(ctx.author.id, 10 * amount)
                gratz = f'Two grapes! User won {10*amount}PPD'
            elif result.count(':grapes:') == 1:
                await self.dbm.eco_add_balance(ctx.author.id, 2 * amount)
                gratz = f'One grape! You won {2*amount}PPD'
            else:
                gratz = f'Nothing! Better luck next time :/'

            await ctx.send(
                f'---------------\n{" ".join(result)}\n---------------\n{gratz}'
            )


def setup(bot):
    bot.add_cog(Gamble(bot))
