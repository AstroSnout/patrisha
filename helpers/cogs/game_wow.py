import discord
from discord.ext import commands
from helpers import util as u
from helpers import cfg, routes
from helpers.ss_maker import Spreadsheets
from helpers.db_manager import DBManager
import operator
import time
import datetime
import xlsxwriter
import json
import base64 as b64


class CharacterNameMissing(Exception):
    pass


class RealmMissing(Exception):
    pass


class RegionMissing(Exception):
    pass


class MythicRun:
    def __init__(self):
        self.realm = None
        self.region = None
        self.dungeon = None
        self.level = None
        self.time = None
        self.tank = None
        self.heal = None
        self.dps1 = None
        self.dps2 = None
        self.dps3 = None


class MythicRunner:
    def __init__(self):
        self.name = None
        self.realm = None
        self.region = None
        self.spec = None
        self.score = None
        self.ilv = None


class MythicUtilities:
    roles = {
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
        'Restoration Druid': 'healer',
        'Resto Druid': 'healer',
        'MW Monk': 'healer',
    }  # As seen on raider.io
    role_icons = {
        'tank': 'https://vignette.wikia.nocookie.net/wowwiki/images/7/7e/Icon-class-role-tank-42x42.png',
        'healer': 'https://vignette.wikia.nocookie.net/wowwiki/images/0/07/Icon-class-role-healer-42x42.png',
        'dps': 'https://vignette.wikia.nocookie.net/wowwiki/images/3/3f/Icon-class-role-dealer-42x42.png'
    }
    specs = {
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
    }  # As seen on bnet
    bfa_dng = [
        'Atal\'dazar',
        'Freehold',
        'Tol Dagor',
        'The MOTHERLODE!!',
        'Waycrest Manor',
        'Kings\' Rest',
        'Temple of Sethraliss',
        'The Underrot',
        'Shrine of the Storm',
        'Siege of Boralus'
    ]
    bfa_dng_short = [
        'ad', 'fh', 'td', 'ml', 'wm', 'kr', 'tos', 'undr', 'sots', 'siege'
    ]


class GameWow:
    def __init__(self, bot):
        self.bot = bot
        self.role_icons = {
            'tank': 'https://vignette.wikia.nocookie.net/wowwiki/images/7/7e/Icon-class-role-tank-42x42.png',
            'healer': 'https://vignette.wikia.nocookie.net/wowwiki/images/0/07/Icon-class-role-healer-42x42.png',
            'dps': 'https://vignette.wikia.nocookie.net/wowwiki/images/3/3f/Icon-class-role-dealer-42x42.png'
        }
        self.dungeon_names = [
            'Atal\'dazar',
            'Freehold',
            'Tol Dagor',
            'The MOTHERLODE!!',
            'Waycrest Manor',
            'Kings\' Rest',
            'Temple of Sethraliss',
            'The Underrot',
            'Shrine of the Storm',
            'Siege of Boralus'
        ]
        self.name_to_abr = {
            'Atal\'dazar': 'AD',
            'Freehold': 'FH',
            'Tol Dagor': 'TD',
            'The MOTHERLODE!!': 'ML',
            'Waycrest Manor': 'WM',
            'Kings\' Rest': 'KR',
            'Temple of Sethraliss': 'ToS',
            'The Underrot': 'UNDR',
            'Shrine of the Storm': 'SotS',
            'Siege of Boralus': 'Siege',
        }
        self.abr_to_name = {
            'ad'   : 'Atal\'dazar',
            'fh'   : 'Freehold',
            'td'   : 'Tol Dagor',
            'ml'   : 'The MOTHERLODE!!',
            'wm'   : 'Waycrest Manor',
            'kr'   : 'Kings\' Rest',
            'tos'  : 'Temple of Sethraliss',
            'undr' : 'The Underrot',
            'sots' : 'Shrine of the Storm',
            'siege': 'Siege of Boralus'
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
            'Restoration Druid': 'healer',
            'Resto Druid': 'healer',
            'MW Monk': 'healer',
        }
        self.dng_abr = ['ad', 'fh', 'td', 'ml', 'wm', 'kr', 'tos', 'undr', 'sots', 'siege']
        self.token = cfg.BNET_ACCESS_TOKEN
        self.api_key = cfg.BNET_API_KEY
        self.db_manager = DBManager()
        self.ss_maker = Spreadsheets()


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
                routes.raider_io.affixes(region)
            )
            # When the request fails for whatever reason
            if 'message' in affixes.keys():
                await ctx.send(affixes['message'])
                return
            # Make an embed object with relevant info
            embed = discord.Embed(
                title=f'This week\'s affixes for {affixes["region"].upper()} region',
                description=affixes['title'].replace(', ', ' > '),
                color=u.color_pick(4300)
            )
            # Add a field to previously created embed for each of the affixes
            for i in range(len(affixes['affix_details'])):
                num = 1 if i == 0 else i*3
                affix = {
                    'name': affixes['affix_details'][i]['name'],
                    'description': affixes['affix_details'][i]['description'],
                    'url': affixes['affix_details'][i]['wowhead_url']
                }
                embed.add_field(
                    name=f'+{num+1} {affix["name"]}',
                    value=f'{affix["description"]} [Read more on Wowhead]({affix["url"]})',
                    inline=False
                )

        await ctx.send(embed=embed)

    @m.command(name='profile', aliases=['rio', 'p'], help='Returns character r.io score, highest scoring runs and recently completed runs')
    async def m_profile(self, ctx, *args):
        try:
            async with ctx.typing():
                print(args)
                realm = await self.db_manager.get_default_realm(ctx.guild)
                region = await self.db_manager.get_default_region(ctx.guild)
                # Args (char_name, realm, region)
                if len(args) == 0:
                    await ctx.send('Input the arguments')
                if len(args) >= 1:
                    char_name = args[0]
                if len(args) >= 2:
                    realm = args[1]
                if len(args) >= 3:
                    region = args[2]
                # Print the requester and command invoked, for logging purposes
                print(f'{ctx.message.author} requested M+ score for {char_name}-{realm}')
                # Request all character data we need
                character_data = await u.get_json(
                    routes.raider_io.all_character_data(char_name, realm, region)
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
                    routes.raider_io.character_profile(char_name, realm, region)
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

                    value_field += '#{} {} +{} in {} (+{} up) **({} points)**\n'.format(
                            i + 1,
                            run["dungeon"],
                            run["level"],
                            run["time"],
                            run["upgrades"],
                            run["score"]
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
                    value_field += '#{} {} +{} in {} (+{} up) **({} points)**\n'.format(
                        i + 1,
                        run["dungeon"],
                        run["level"],
                        run["time"],
                        run["upgrades"],
                        run["score"]
                    )

                embed.add_field(
                    name='__Recently completed runs__',
                    value=value_field,
                    inline=False
                )
                # Thank the Raider.io team for their great work
                embed.set_footer(text='Click the character name to see their raider.io profile. All data is taken from raider.io',)
            await ctx.send(embed=embed)
        except discord.errors.HTTPException:
            await ctx.send('Character found, but no raider.io profile is available')
        except ValueError:
            await ctx.send('Command format is the following:\n```!m rio <character name> <realm> <region>\nRealm defaults to Kazzak\nRegion defaults to EU```')

    @m.command(name='last', aliases=['worst', 'l', 'w'], help='See what the last (most of the time 500th) run is on the official leaderboards')
    async def m_last(self, ctx, *args):
        try:
            async with ctx.typing():
                print(args)
                if ctx.guild:
                    user_realm = await self.db_manager.get_default_realm(ctx.guild)
                else:
                    user_realm = 'kazzak'
                dungeon = 'all'
                # Args (char_name, realm, region)
                if len(args) == 0:
                    await ctx.send(f'No input - using default realm for this server - `{user_realm.title()}(EU)`')
                if len(args) >= 1:
                    user_realm = args[0]
                if len(args) >= 2:
                    dungeon = args[1]
                print(f'{ctx.message.author} requested last dungeon({dungeon}) on realm({user_realm})')
                # TODO- Line below throws TypeError: 'NoneType' object is not iterable
                current_leaderboards, realm_name = await self.m_leaderboards(ctx, 'last', user_realm, dungeon)
                dungeon_name = current_leaderboards['map']['name']
                # Extract the affixes from the BNET response, so we can avoid making another one
                affixes = [current_leaderboards['keystone_affixes'][x]['keystone_affix']['name'] for x in range(3)]
                # Assign variables for increased readability
                last_group = current_leaderboards['leading_groups'][-1]
                keystone_level = last_group['keystone_level']
                duration = time.strftime("%H:%M:%S", time.gmtime(last_group['duration'] // 1000))
                # Make an embed object with relevant info
                embed = discord.Embed(
                    title='{} > {} > {}'.format(affixes[0], affixes[1], affixes[2]),
                    description='Do a +{} under {} or a greater keystone level'.format(keystone_level, duration),
                    color=u.color_pick(1500)
                )
                # Set requested run as author so we can put a pretty little icon
                embed.set_author(
                    name='Last ranked run for {} on {}'.format(dungeon_name, realm_name),
                    icon_url='https://cdn0.iconfinder.com/data/icons/large-weather-icons/256/Heat.png'
                )
                # Print the requester and command invoked, for logging purposes
                print(ctx.message.author, 'requested the last run for {} on {}'.format(dungeon_name, realm_name))
                await ctx.send(embed=embed)
        except TypeError:
            pass
        except ValueError:
            await ctx.send('Command format is the following:\n```!m last <realm name> <dungeon name/all>```')

    @m.command(name='first', aliases=['best', 'f', 'b'], help='See what the best run is on the official leaderboards')
    async def m_first(self, ctx, *args):
        try:
            async with ctx.typing():
                print(args)
                if ctx.guild:
                    user_realm = await self.db_manager.get_default_realm(ctx.guild)
                    if user_realm is None:
                        await ctx.send('No default realm set ofr this server, using bot default instead.')
                        user_realm = 'kazzak'
                else:
                    user_realm = 'kazzak'
                dungeon = 'all'
                # Args (char_name, realm, region)
                if len(args) == 0:
                    await ctx.send(f'No input - using default realm for this server - `{user_realm.title()}(EU)`')
                if len(args) >= 1:
                    user_realm = args[0]
                if len(args) >= 2:
                    dungeon = args[1]
                print(f'{ctx.message.author} requested first dungeon({dungeon}) on realm({user_realm})')
                current_leaderboards, realm_name = await self.m_leaderboards(ctx, 'first', user_realm, dungeon)
                dungeon_name = current_leaderboards['map']['name']
                # Extract the affixes from the BNET response, so we can avoid making another one
                affixes = [current_leaderboards['keystone_affixes'][x]['keystone_affix']['name'] for x in range(3)]
                # Assign variables for increased readability
                leading_group = current_leaderboards['leading_groups'][0]
                keystone_level = leading_group['keystone_level']
                duration = time.strftime("%H:%M:%S", time.gmtime(leading_group['duration'] // 1000))
                members = leading_group['members']
                my_members = [None, None]
                # Extract the group info so we can send a more detailed embed
                for mmbr in members:
                    # Your generic party member model
                    member = {
                        'name': mmbr['profile']['name'],
                        'realm': mmbr['profile']['realm']['slug'],
                        'spec': self.specs[str(mmbr['specialization']['id'])],
                        'role': '',
                        'mscore': 0
                    }
                    print(member['spec'])
                    # Find the party member's role in that run
                    if self.roles.get(member['spec']) == 'healer':
                        member['role'] = 'Healer'
                        my_members[1] = member
                    elif self.roles.get(member['spec']) == 'tank':
                        member['role'] = 'Tank'
                        my_members[0] = member
                    else:
                        member['role'] = 'DPS'
                        my_members.append(member)
                    # Get the member's M+ score for **even more** detail
                    mscore = await u.get_json(
                        routes.raider_io.mythic_score(mmbr['profile']['name'], mmbr['profile']['realm']['slug'], 'eu')
                    )
                    # Assign the obtained score to our model
                    member['mscore'] = mscore['mythic_plus_scores']['all']

                # Make an embed object with relevant info
                embed = discord.Embed(
                    title='{} > {} > {}'.format(affixes[0], affixes[1], affixes[2]),
                    description='Completed +{} in {}'.format(keystone_level, duration),
                    color=u.color_pick(5500)
                )
                # Set requested run as author so we can put a pretty little icon
                embed.set_author(
                    name='Top Run for {} on {}'.format(dungeon_name, realm_name),
                    icon_url='http://www.myiconfinder.com/uploads/iconsets/256-256-6fc6f09b8c986ade7286aa71ba43c71e-trophy.png'
                )
                # We don't know something :/
                for member in my_members:
                    if member is None:
                        if len(my_members) == 5:
                            member = {
                                'role': 'Unknown',
                                'spec': 'Unknown',
                                'realm': 'Unknown',
                                'name': 'Unknown',
                                'mscore': 0
                            }
                        else:
                            continue
                    # Make a field for every party member with some details
                    embed.add_field(
                        name='{} ({})'.format(member['role'], member['spec']),
                        value='[{}](https://raider.io/characters/eu/{}/{})'.format(member['name'], member['realm'],
                                                                                   member['name'])
                    )
                # Calculate the average group M+ score
                print(my_members)
                mscore_avg = 'Unknown' if None in my_members else sum([member['mscore'] for member in my_members]) // 5
                embed.add_field(
                    name='Group average M+ score:',
                    value=mscore_avg
                )
                # Set the faction icon so it looks pretty
                faction_icon = 'https://assets.raider.io/images/site/horde_logo_xs.png' \
                    if members[0]['faction']['type'] == 'HORDE' \
                    else 'https://assets.raider.io/images/site/alliance_logo_xs.png'
                embed.set_thumbnail(
                    url=faction_icon
                )

                # Print the requester and command invoked, for logging purposes
                print(ctx.message.author, 'requested the last run for {} on {}'.format(dungeon_name, realm_name))
                await ctx.send(embed=embed)
        except TypeError:
            pass
        except Exception:
            await ctx.send('Command format is the following:\n```!m first <realm name> <dungeon name/all>```')

    @commands.group(name='guild', invoke_without_command=True, help='Command subgroup for WoW\'s guilds')
    async def guild(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid Guild command passed...')

    @guild.command(name='sub', help='Subscribes the user to recieve updates relating to roster changes of the specified guild')
    async def guild_sub(self, ctx, realm_name, *guild_name):
        guild_name = ' '.join(guild_name).lower()
        print(f'{ctx.message.author} subbed to {guild_name} on realm({realm_name})')
        # Get members of a guild from WoW API
        current_guild_roster = await u.get_guild_roster(realm_name, guild_name)  # WoW API Roster Count
        # get_guild_roster() returns 404 if guild or realm are not found
        if current_guild_roster[0] == 404:
            await ctx.send('Server or Guild not found')
            return
        # Check if the user that invoked the command already exists in DB for specified guild on specified realm
        added = await self.db_manager.guild_sub(ctx.message.author.id, realm_name, guild_name)
        if added:
            await ctx.send('Subscribed to recieve roster changes in {} on {}'.format(guild_name.title(), realm_name.title()))
        else:
            await ctx.send('Already subscribed to that guild')

    @guild.command(name='unsub', help='Unsubscribes the user from a specified guild they are subbed to')
    async def guild_unsub(self, ctx, realm_name, *guild_name):
        guild_name = ' '.join(guild_name).lower()
        print(f'{ctx.message.author} unsubbed to {guild_name} on realm({realm_name})')
        # Get members of a guild from WoW API
        current_guild_roster = await u.get_guild_roster(realm_name, guild_name)  # WoW API Roster Count
        # get_guild_roster() returns 404 if guild or realm are not found
        if current_guild_roster[0] == 404:
            await ctx.send('Server or Guild not found')
            return
        # Check if the user that invoked the command already exists in DB for specified guild on specified realm
        removed = await self.db_manager.guild_unsub(ctx.message.author.id, realm_name, guild_name)
        if removed:
            await ctx.send('Unsubscribed to {} on {}'.format(guild_name.title(), realm_name.title()))
        else:
            await ctx.send('You are not subbed to that guild')

    @commands.command(name='token', help='See the current token price (EU/US/KR/TW)')
    async def tok(self, ctx, region: str = 'EU'):
        async with ctx.typing():
            # for r in ['eu', 'kr', 'us', 'tw']:
            #     await self.db_manager.update_token(r)
            # return
            print(f'{ctx.message.author} requested token price for region {region}')
            region_list = ['EU', 'US', 'KR', 'TW']
            if region.upper() not in region_list:
                await ctx.send('Region {} is not supported. Try EU, US, KR or TW (not case sensitive)'.format(region))
                return
            region = region.lower()
            # Check if DB is up to date
            current_token_json = await self.db_manager.db_token['token_current'].find_one({"region": region.lower()})
            print('Current Token = ', current_token_json)
            # Last updated posix time
            json_posix_time = current_token_json['last_updated'] / 1000
            # Current posix time
            current_posix_time = time.time()
            # Compares the two
            if current_posix_time - json_posix_time > 2400:
                current_token_json = await self.db_manager.update_token(region)  # Returns the token it posted to DB
                print('{} region database has been updated!'.format(region.upper()))
            else:
                print('Database is up to date')

            # Time formatting is hard
            last_updated = datetime.datetime.utcfromtimestamp(current_token_json['last_updated'] / 1000 + 7200).strftime(
                '%B %d, %Y at %H:%M:%S')
            await ctx.send('Current **{0}** token price: **{1} {3}** \n_Last updated: {2} GMT+1_'
                           .format(
                                region.upper(),
                                current_token_json['price'],
                                last_updated,
                                u.get_emoji('goldcoins')
                           ))

    async def m_leaderboards(self, ctx, call_type, user_realm, dungeon):
        # Request realm info
        try:
            realm = await u.get_json(
                routes.blizzard.realm(user_realm)
            )
            # Assign new variables for increased readability
            realm_name = realm['name']
            realm_id = realm['id']
        except:
            await ctx.send(f'Can\'t find realm `{user_realm}`')
            return
        # Call a separate function if user requests all dungeons (written near the end of this class)
        if dungeon.lower() == 'all':
            if call_type == 'last':
                await self.m_last_all(ctx, realm_id, realm_name)
                return
            else:
                await self.m_first_all(ctx, realm_id, realm_name)
                return
        # Makes lowercase names from our list
        lowercase_dungeons = list(map(str.lower, self.dungeon_names))
        # The following statements enable partial and abbreviated input (i.e. 'eoa or 'eye' for Eye of Azshara)
        dungeon_name = ''
        # See if the name is possibly abbreviated (i.e. 'eoa' for 'Eye of Azshara')
        if dungeon.lower() in self.dng_abr:
            dungeon_name = self.abr_to_name[dungeon.lower()]
        # See if it's actually full dungeon name
        elif dungeon.lower() in lowercase_dungeons:
            dungeon_name = dungeon
        # See if it's a partial match (i.e. 'eye' for 'Eye of Azshara')
        else:
            for item in lowercase_dungeons:
                if dungeon.lower() in item:
                    dungeon_name = item.title()
                    break
            # If we found nothing above
            if dungeon_name == '':
                await ctx.send(f'Can\'t find {dungeon} in dungeons')
                return
        # Request all dungeons' info
        dungeons = await u.get_json(
            routes.blizzard.dungeons(realm_id)
        )
        # Assign variable for increased readability
        all_leaderboards = dungeons['current_leaderboards']
        # Request leaderboards for specified dungeon
        for dgn in all_leaderboards:
            if dgn['name'].lower() == dungeon_name.lower():
                current_leaderboards = await u.get_json(
                    dgn['key']['href'] + '&locale=en_GB&access_token=' + self.token
                )
                if type(current_leaderboards) is not dict:
                    await ctx.send(f'Oh-oh! Error {current_leaderboards} has occured :(')
                    return
                break

        return current_leaderboards, realm_name

    async def m_last_all(self, ctx, realm_id, realm_name):
        print(f'{ctx.message.author} requested last place for all dungeons')
        warning_text = '**Warning:** _Due to the number of successive requests made to the Blizzard API,' \
                       ' this command has a high chance of timing out. ' \
                       'Consider requesting a specific dungeon instead._'
        bot_msg = await ctx.send(
            warning_text
        )
        await ctx.trigger_typing()

        # Dungeon API
        dungeons = await u.get_json(
            routes.blizzard.dungeons(realm_id)
        )
        all_leaderboards = dungeons['current_leaderboards']

        lb_embed = discord.Embed(
            title=' ',
            description=' ',
            color=0xfe49ab
        )
        lb_embed.set_author(
            name='Lowest keystones ranked on the leaderboard for {}'.format(realm_name),
            url='https://raider.io/mythic-plus/realms/eu/current',
            icon_url='https://media.forgecdn.net/avatars/117/23/636399071197048271.png'
        )

        # Cycle through the JSON containing URIs to dungeon leaderboards to get the info needed
        for lb in all_leaderboards:
            uri = lb['key']['href'] + '&locale=en_GB&access_token={}'.format(self.token)

            await bot_msg.edit(content=warning_text + f'\n**Requesting dungeon:** {lb["name"]}')
            # Request the URI for a dungeon leaderboard
            try:
                groups = await u.get_json(
                    uri
                )
            except:
                await bot_msg.edit(content='An error has occured, try querying a specific dungeon instead! :)')
                print('Failed to retrieve', lb['name'])
                return

            while groups == 504:
                groups = await u.get_json(
                    uri
                )

            try:
                groups = groups['leading_groups']
            except KeyError:
                break

            if len(groups) < 500:
                lb_embed.add_field(
                    name='{}'.format(lb['name']),
                    value='> {} spots remaining'.format(500 - len(groups)),
                    inline=True
                )

            # Adds a field for the last placed team
            else:
                worst_run = groups[-1]
                time_str = time.strftime("%H:%M:%S", time.gmtime(worst_run['duration'] // 1000))
                lb_embed.add_field(
                    name='{}'.format(lb['name']),
                    value='> +{} in {}'.format(worst_run['keystone_level'], time_str),
                    inline=True
                )

        # Send the results to the user (Edits the first bot message)
        await bot_msg.delete()
        await ctx.send(content='I\'m done, {}!'.format(ctx.message.author.mention), embed=lb_embed)
        # TODO - caching the list

    async def m_first_all(self, ctx, realm_id, realm_name):
        print(f'{ctx.message.author} requested first place for all dungeons')
        warning_text = '**Warning:** _Due to the number of successive requests made to the Blizzard API,'\
                       ' this command has a high chance of timing out. '\
                       'Consider requesting a specific dungeon instead._'
        bot_msg = await ctx.send(
            warning_text
        )
        await ctx.trigger_typing()

        # Dungeon API
        dungeons = await u.get_json(
            routes.blizzard.dungeons(realm_id)
        )
        all_leaderboards = dungeons['current_leaderboards']

        lb_embed = discord.Embed(
            title=' ',
            description=' ',
            color=0x035132
        )
        lb_embed.set_author(
            name='Top runs ranked on the leaderboard for {}\n\n'.format(realm_name),
            url='https://worldofwarcraft.com/en-gb/game/pve/leaderboards/{}/'.format(realm_name),
            icon_url='https://media.forgecdn.net/avatars/117/23/636399071197048271.png'
        )

        # Cycle through the JSON containing URIs to dungeon leaderboards to get the info needed
        ''''''
        for lb in all_leaderboards:
            uri = lb['key']['href'] + '&locale=en_GB&access_token={}'.format(self.token)

            await bot_msg.edit(content=warning_text + f'\n**Requesting dungeon:** {lb["name"]}')
            # Request the URI for a dungeon leaderboard
            try:
                groups = await u.get_json(
                    uri
                )
            except:
                await bot_msg.edit(content='An error has occured, try querying a specific dungeon instead! :)')
                print('Failed to retrieve', lb['name'])
                return

            while groups == 504:
                groups = await u.get_json(
                    uri
                )
            try:
                groups = groups['leading_groups']
            except KeyError:
                break

            best_run = groups[0]
            time_str = time.strftime("%H:%M:%S", time.gmtime(best_run['duration'] // 1000))
            lb_embed.add_field(
                name='{}'.format(lb['name']),
                value='> +{} in {}'.format(best_run['keystone_level'], time_str),
                inline=True
            )

        lb_embed.set_footer(
            text='Try !m first {} <dungeon> to get more details on the run!'.format(realm_name),
        )

        # Send the results to the user (Edits the first bot message)
        await bot_msg.delete()
        await ctx.send(content='I\'m done, {}!'.format(ctx.message.author.mention), embed=lb_embed)
        # TODO - caching the list


def setup(bot):
    bot.add_cog(GameWow(bot))
