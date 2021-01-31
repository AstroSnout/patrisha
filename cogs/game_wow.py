import discord
from discord.ext import commands
from helpers import util as u
from helpers import routes

import operator
import time


class GameWow(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.role_icons = {
            'tank': 'https://vignette.wikia.nocookie.net/wowwiki/images/7/7e/Icon-class-role-tank-42x42.png',
            'healer': 'https://vignette.wikia.nocookie.net/wowwiki/images/0/07/Icon-class-role-healer-42x42.png',
            'dps': 'https://vignette.wikia.nocookie.net/wowwiki/images/3/3f/Icon-class-role-dealer-42x42.png'
        }
        self.dungeon_names = [
            'De Other Side',
            'Halls of Atonement',
            'Mists of Tirna Scithe',
            'Plaguefall',
            'Sanguine Depths',
            'Spires of Ascension',
            'The Necrotic Wake',
            'Theater of Pain',
        ]
        self.name_to_abr = {
            'De Other Side': 'DS',
            'Halls of Atonement': 'HoA',
            'Mists of Tirna Scithe': 'MISTS',
            'Plaguefall': 'PF',
            'Sanguine Depths': 'SD',
            'Spires of Ascension': 'SoA',
            'The Necrotic Wake': 'NW',
            'Theater of Pain': 'ToP',
        }
        self.abr_to_name = {
            'ds'   : 'De Other Side',
            'hoa'  : 'Halls of Atonement',
            'mists': 'Mists of Tirna Scithe',
            'pf'   : 'Plaguefall',
            'sd'   : 'Sanguine Depths',
            'soa'  : 'Spires of Ascension',
            'nw'   : 'The Necrotic Wake',
            'top'  : 'Theater of Pain',
        }
        self.specs = {
            '250': 'Blood DK',
            '251': 'Frost DK',
            '252': 'Unholy DK',
            '577': 'Havoc DH',
            '581': 'Vengeance DH',
            '102': 'Balance Druid',
            '103': 'Feral Druid',
            '104': 'Guardian Druid',
            '105': 'Resto Druid',
            '253': 'BM Hunter',
            '254': 'MM Hunter',
            '255': 'Survival Hunter',
            '62': 'Arcane Mage',
            '63': 'Fire Mage',
            '64': 'Frost Mage',
            '268': 'Brewmaster Monk',
            '269': 'WW Monk',
            '270': 'MW Monk',
            '65': 'Holy Paladin',
            '66': 'Prot Paladin',
            '70': 'Retri Paladin',
            '256': 'Disc Priest',
            '257': 'Holy Priest',
            '258': 'Shadow Priest',
            '259': 'Assa Rogue',
            '260': 'Outlaw Rogue',
            '261': 'Sub Rogue',
            '262': 'Elemental Shaman',
            '263': 'Enha Shaman',
            '264': 'Resto Shaman',
            '265': 'Affli Warlock',
            '266': 'Demo Warlock',
            '267': 'Destro Warlock',
            '71': 'Arms Warrior',
            '72': 'Fury Warrior',
            '73': 'Prot Warrior',
        }
        self.roles = {
            'Blood DK': 'tank',
            'Vengeance DH': 'tank',
            'Guardian Druid': 'tank',
            'Brewmaster Monk': 'tank',
            'Protection Paladin': 'tank',
            'Protection Warrior': 'tank',
            'Restoration Shaman': 'healer',
            'Holy Priest': 'healer',
            'Disc Priest': 'healer',
            'Holy Paladin': 'healer',
            'Mistweaver Monk': 'healer',
            'Restoration Druid': 'healer'
        }
        self.dng_abr = ['ds', 'hoa', 'mists', 'pf', 'sd', 'soa', 'nw', 'top']

    @commands.group(name='m', invoke_without_command=True, help='WoW\'s Mythic Plus related commands')
    async def m(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.invoke(self.bot.get_command('help'), 'm')

    @m.command(name='affix', aliases=['affixes', 'aff', 'a'], help='See what this week\'s affixes are')
    async def m_affixes(self, ctx, *, region: str = 'eu'):
        async with ctx.typing():
            # Print the requester and command invoked, for logging purposes
            print(f'{ctx.message.author} requested this week\'s affixes for region {region.upper()}')
            # Request mythic affixes
            affixes = await u.get_json(
                routes.RaiderIORoutes.affixes(region)
            )
            # When the request fails for whatever reason
            if 'message' in affixes.keys():
                await ctx.send(affixes['message'])
                return
            # Make an embed object with relevant info
            embed = discord.Embed(
                title=f'This week\'s affixes for {affixes["region"].upper()} region',
                description=affixes['title'].replace(', ', '  '),
                color=u.color_pick(4300)
            )
            # Add a field to previously created embed for each of the affixes
            for i in range(len(affixes['affix_details'])):
                embed.add_field(
                    name=f'+{i*3+2} {affixes["affix_details"][i]["name"]}',
                    value=f'{affixes["affix_details"][i]["description"]} [Read more on Wowhead]({affixes["affix_details"][i]["wowhead_url"]})',
                    inline=False
                )

        await ctx.send(embed=embed)

    @m.command(name='profile', aliases=['rio', 'p'], help='Returns character r.io score, highest scoring runs and recently completed runs')
    async def m_profile(self, ctx, char_name: str, realm: str, region: str = 'eu'):
        async with ctx.typing():
            # Print the requester and command invoked, for logging purposes
            print(f'{ctx.message.author} requested M+ score for {char_name}-{realm}')
            # Request all character data we need
            character_data = await u.get_json(
                routes.RaiderIORoutes.all_character_data(char_name, realm, region)
            )
            # When the request fails for whatever reason
            if 'message' in character_data.keys():
                await ctx.send(character_data['message'])
                return

            # Assign new variables for increased readability
            m_score_total = character_data['mythic_plus_scores'].pop('all', None)
            # Assign variable for increased readability
            recent_runs = character_data['mythic_plus_recent_runs']
            role = max(character_data['mythic_plus_scores'].items(), key=operator.itemgetter(1))[0]  # Role with best score
            # Request top dungeon runs (currently the r.io API only returns the top 3)
            character = await u.get_json(
                routes.RaiderIORoutes.character_profile(char_name, realm, region)
            )
            # Make an embed object with relevant info
            embed = discord.Embed(
                title=' ',
                description=' ',
                color=u.color_pick(m_score_total)
            )
            # Set the thumbnail obtained from the character profile
            embed.set_thumbnail(url=character['thumbnail_url'])
            # Set requested character as author so we can link to their profile
            embed.set_author(
                name='[{}] {}-{}'.format(character['class'], character['name'], character['realm']),
                url=character['profile_url'],
                icon_url=self.role_icons[role]
            )
            # Set their mythic plus score field to the obtained value
            embed.add_field(name='Mythic+ Score:', value='({} points)'.format(m_score_total), inline=True)
            # Show their equipped itemlevel
            embed.add_field(name='Equipped iLvl:', value=character_data['gear']['item_level_equipped'], inline=True)
            # Assign new variable for increased readability
            best_runs = character['mythic_plus_best_runs']
            # Add a field to the embed for every run the API returned (that's 3 most of the time)
            value_field = ''

            # Best runs field
            for i in range(len(best_runs)):
                run = {
                    'dungeon': self.name_to_abr[best_runs[i]['dungeon']],  # Translate abr to full name
                    'level': best_runs[i]['mythic_level'],
                    'upgrades': best_runs[i]['num_keystone_upgrades'],
                    'time': time.strftime("%H:%M:%S", time.gmtime(best_runs[i]['clear_time_ms'] // 1000)),
                    'score': best_runs[i]['score']
                }

                value_field += '`#{:<2} {:^5}  +{:<2} in {} (+{} up) ({:^5} points)`\n'.format(
                        i + 1,
                        run["dungeon"],
                        run["level"],
                        run["time"],
                        run["upgrades"],
                        float(run["score"])
                )

            embed.add_field(
                name='__Highest scoring runs__',
                value=value_field,
                inline=False
            )
            # Recent runs field
            value_field = ''
            for i in range(len(recent_runs)):
                run = {
                    'dungeon': self.name_to_abr[recent_runs[i]['dungeon']],  # Translate abr to full name
                    'level': recent_runs[i]['mythic_level'],
                    'upgrades': recent_runs[i]['num_keystone_upgrades'],
                    'time': time.strftime("%H:%M:%S", time.gmtime(recent_runs[i]['clear_time_ms'] // 1000)),
                    'score': recent_runs[i]['score']
                }
                value_field += '`#{:<2} {:^5}  +{:<2} in {} (+{} up) ({:^5} points)`\n'.format(
                    i + 1,
                    run["dungeon"],
                    run["level"],
                    run["time"],
                    run["upgrades"],
                    float(run["score"])
                )

            embed.add_field(
                name='__Recently completed runs__',
                value=value_field,
                inline=False
            )
            # Thank the Raider.io team for their great work
            embed.set_footer(text='Click the character name to see their raider.io profile. All data is taken from raider.io',)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(GameWow(bot))
