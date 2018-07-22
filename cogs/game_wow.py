import discord
from discord.ext import commands
from helpers import util as u
from helpers import cfg, routes
from helpers.db_manager import DBManager
import operator
import time
import datetime
import xlsxwriter


class GameWow:

    def __init__(self, bot):
        self.bot = bot
        self.role_icons = {
            'tank': 'https://vignette.wikia.nocookie.net/wowwiki/images/7/7e/Icon-class-role-tank-42x42.png',
            'healer': 'https://vignette.wikia.nocookie.net/wowwiki/images/0/07/Icon-class-role-healer-42x42.png',
            'dps': 'https://vignette.wikia.nocookie.net/wowwiki/images/3/3f/Icon-class-role-dealer-42x42.png'
        }
        self.name_to_abr = {
            'Black Rook Hold': 'BRH',
            'Cathedral of Eternal Night': 'CoEN',
            'Court of Stars': 'CoS',
            'Darkheart Thicket': 'DHT',
            'Eye of Azshara': 'EoA',
            'Halls of Valor': 'HoV',
            'Maw of Souls': 'MoS',
            'Neltharion\'s Lair': 'NL',
            'Return to Karazhan: Lower': 'LOWR',
            'Return to Karazhan: Upper': 'UPPR',
            'Seat of the Triumvirate': 'SEAT',
            'The Arcway': 'Arc',
            'Vault of the Wardens': 'VotW'
        }
        self.abr_to_name = {
            'brh'   :   'Black Rook Hold',
            'coen'  :   'Cathedral of Eternal Night',
            'cos'   :   'Court of Stars',
            'dht'   :   'Darkheart Thicket',
            'eoa'   :   'Eye of Azshara',
            'hov'   :   'Halls of Valor',
            'mos'   :   'Maw of Souls',
            'nl'    :   'Neltharion\'s Lair',
            'lower' :   'Return to Karazhan: Lower',
            'upper' :   'Return to Karazhan: Upper',
            'seat'  :   'Seat of the Triumvirate',
            'arc'   :   'The Arcway',
            'vault' :   'Vault of the Wardens',
            'votw'  :   'Vault of the Wardens'
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
        self.dng_abr = ['brh', 'coen', 'cos', 'dht', 'eoa', 'hov', 'mos', 'nl', 'lower', 'upper', 'seat', 'arc', 'vault', 'votw']
        self.token = cfg.BNET_ACCESS_TOKEN
        self.api_key = cfg.BNET_API_KEY
        self.db_manager = DBManager()

    @commands.group(name='m', invoke_without_command=True, help='WoW\'s Mythic Plus related commands')
    async def m(self, ctx):
        if ctx.invoked_subcommand is None:
            raise Exception

    @m.command(name='affix', aliases=['affixes', 'aff'], help='See what this week\'s affixes are')
    async def m_affixes(self, ctx, *, region: str = 'eu'):
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
            title='This week\'s affixes for {} region'.format(affixes['region'].upper()),
            description=affixes['title'].replace(', ', ' > '),
            color=u.color_pick(4300)
        )
        # Add a field to previously created embed for each of the affixes
        for i in range(3):
            embed.add_field(
                name='+{} {}'.format(i * 3 + 4, affixes['affix_details'][i]['name']),
                value='{} [Read more on Wowhead]({})'.format(affixes['affix_details'][i]['description'],
                                                             affixes['affix_details'][i]['wowhead_url']),
                inline=False
            )
        # Print the requester and command invoked, for logging purposes
        print(ctx.message.author, 'requested this week\'s affixes for region {}'.format(affixes['region'].upper()))
        await ctx.send(embed=embed)

    @m.command(name='score', help='Check a specified character\'s score, alongside some other minor info')
    async def m_score(self, ctx, char_name: str, realm: str, region: str = 'eu'):
        # Request mythic scores
        m_score = await u.get_json(
            routes.raider_io.mythic_score(char_name, realm, region)
        )
        # When the request fails for whatever reason
        if 'message' in m_score.keys():
            await ctx.send(m_score['message'])
            return
        # Assign new variables for increased readability
        m_score_total = m_score['mythic_plus_scores'].pop('all', None)
        role = max(m_score['mythic_plus_scores'].items(), key=operator.itemgetter(1))[0]  # Role with best score
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
        embed.add_field(name='Mythic+ Score:', value='({} points)'.format(m_score_total), inline=False)
        # Assign new variable for increased readability
        best_runs = character['mythic_plus_best_runs']
        # Add a field to the embed for every run the API returned (that's 3 most of the time)
        for i in range(len(best_runs)):
            # Convert to pretty time
            clear_time = time.strftime("%H:%M:%S", time.gmtime(best_runs[i]['clear_time_ms'] // 1000))
            embed.add_field(
                name='#{} {} +{} in {} (+{} up)'.format(
                    i + 1,
                    self.name_to_abr[best_runs[i]['dungeon']],
                    best_runs[i]['mythic_level'],
                    clear_time,
                    best_runs[i]['num_keystone_upgrades']
                ),
                value='>> * {} points *'.format(best_runs[i]['score']),
                inline=False
            )
        # Thank the Raider.io team for their great work
        embed.set_footer(text='Click the character name to see his raider.io profile. All data is taken from raider.io',)
        # Print the requester and command invoked, for logging purposes
        print(ctx.message.author, 'requested M+ score for', character['name'] + '-' + character['realm'])
        await ctx.send(embed=embed)

    @m.command(name='last', help='See what the last (most of the time 500th) run is on the official leaderboards')
    async def m_last(self, ctx, realm, *, dungeon: str = 'all'):
        print('Getting the last dungeon on the leaderboard')
        print(list(self.abr_to_name.values()), self.abr_to_name.keys())
        # Request realm info
        realm = await u.get_json(
            routes.blizzard.realm(realm)
        )
        # Assign new variables for increased readability
        realm_name = realm['name']
        realm_id = realm['id']
        # Call a separate function if user requests all dungeons (written near the end of this class)
        if dungeon.lower() == 'all':
            await self.m_last_all(ctx, realm_id, realm_name)
            return
        # Makes lowercase names from our translation dict
        full_names_lower = list(map(str.lower, list(self.abr_to_name.values())))
        # The following statements enable partial and abbreviated input (i.e. 'eoa or 'eye' for Eye of Azshara)
        dungeon_name = ''
        # See if the name is possibly abbreviated (i.e. 'eoa' for 'Eye of Azshara')
        if dungeon.lower() in self.dng_abr:
            dungeon_name = self.abr_to_name[dungeon.lower()]
        # See if it's actually full dungeon name
        elif dungeon.lower() in full_names_lower:
            dungeon_name = dungeon
        # See if it's a partial match (i.e. 'eye' for 'Eye of Azshara')
        else:
            for item in full_names_lower:
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
                try:
                    current_leaderboards = await u.get_json(
                        dgn['key']['href'] + '&locale=en_GB&access_token=' + self.token
                    )
                    if type(current_leaderboards) is not dict:
                        await ctx.send(f'Oh-oh! Error {current_leaderboards} has occured :(')
                        return
                except ValueError:
                    print('exception lul')
                    return
                break

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

    @m.command(name='first', help='See what the best run is on the official leaderboards')
    async def m_first(self, ctx, realm, *, dungeon: str = 'all'):
        # Request realm info
        realm = await u.get_json(
            routes.blizzard.realm(realm)
        )
        # Assign new variables for increased readability
        realm_name = realm['name']
        realm_id = realm['id']
        # Call a separate function if user requests all dungeons (written near the end of this class)
        if dungeon.lower() == 'all':
            await self.m_first_all(ctx, realm_id, realm_name)
            return
        # Makes lowercase names from our translation dict
        full_names_lower = list(map(str.lower, list(self.abr_to_name.values())))
        # The following statements enable partial and abbreviated input (i.e. 'eoa or 'eye' for Eye of Azshara)
        dungeon_name = ''
        # See if the name is possibly abbreviated (i.e. 'eoa' for 'Eye of Azshara')
        if dungeon.lower() in self.dng_abr:
            dungeon_name = self.abr_to_name[dungeon.lower()]
        # See if it's actually full dungeon name
        elif dungeon.lower() in full_names_lower:
            dungeon_name = dungeon
        # See if it's a partial match (i.e. 'eye' for 'Eye of Azshara')
        else:
            for item in full_names_lower:
                if dungeon.lower() in item:
                    dungeon_name = item.title()
                    break
            # If we found nothing above
            if dungeon_name == '':
                await ctx.send('Can\'t find {} in dungeons'.format(dungeon))
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
                try:
                    current_leaderboards = await u.get_json(
                        dgn['key']['href'] + '&locale=en_GB&access_token=' + self.token
                    )
                    if type(current_leaderboards) is not dict:
                        await ctx.send(f'Oh-oh! Error {current_leaderboards} has occured :(')
                        return
                except ValueError:
                    print('exception lul')
                    return
                break

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

    @m.command(name='recent', help='List out character\'s last 3 finished mythic plus dungeons that ranked on the official leaderboards')
    async def recent_mythic(self, ctx, char_name: str, realm: str, region: str = 'eu'):
        # Request mythic scores
        recent = await u.get_json(
            routes.raider_io.recent_runs(char_name, realm, region)
        )
        # When the request fails for whatever reason
        if 'message' in recent.keys():
            await ctx.send(recent['message'])
            return
        # Assign variable for increased readability
        recent_runs = recent['mythic_plus_recent_runs']
        # Make an embed object with relevant info
        embed = discord.Embed(
            title='[{}] {}-{}'.format(recent['class'], recent['name'], recent['realm']),
            description='Last three completed runs:',
            color=u.color_pick(6500)
        )
        # Set a thumbnail for the embed
        embed.set_thumbnail(url=recent['thumbnail_url'])
        # Add fields to the embed for each of the runs returned
        for i in range(len(recent_runs)):
            # Convert to pretty time
            clear_time = time.strftime("%H:%M:%S", time.gmtime(recent_runs[i]['clear_time_ms'] // 1000))
            embed.add_field(
                name='#{} {} +{} in {} (+{} up)'.format(
                    i + 1,
                    self.name_to_abr[recent_runs[i]['dungeon']],
                    recent_runs[i]['mythic_level'],
                    clear_time,
                    recent_runs[i]['num_keystone_upgrades']
                ),
                value='>> * {} points *'.format(recent_runs[i]['score']),
                inline=False
            )

        # Print the requester and command invoked, for logging purposes
        print(ctx.message.author, 'requested mrecent for', recent['name'] + '-' + recent['realm'])
        await ctx.send(embed=embed)

    @commands.group(name='guild', invoke_without_command=True, help='Command subgroup for WoW\'s guilds')
    async def guild(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid Guild command passed...')

    @guild.command(name='sub', help='Subscribes the user to recieve updates relating to roster changes of the specified guild')
    async def guild_sub(self, ctx, realm_name, *guild_name):
        guild_name = ' '.join(guild_name).lower()
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

    @guild.command(name='ss', help='Processes import string from the Add-on to form a spreadsheet')
    async def guild_ss(self, ctx, *import_string):
        # Translate WoW's invite IDs to readable strings
        INV_TRANSLATOR = {
            1: 'Invited',
            2: 'Accepted',
            3: 'Declined',
            4: 'Confirmed',
            5: 'Out',
            6: 'Standby',
            7: 'Signed Up',
            8: 'Not Signed Up',
            9: 'Tentative'
        }
        # Prepare string for parsing
        input_invitees = [x.split(';') for x in ' '.join(import_string).split(';--end--;') if x is not '']
        # Extract event date and title
        input_event_info = input_invitees.pop(0)
        event_info = {}
        for info in input_event_info:
            k, v = info.rsplit(':', 1)
            event_info[k] = v
        # Generate a dict with the invitees
        invitees = []
        invitee = {}
        for inv in input_invitees:
            for attribute in inv:
                a, b = attribute.split(':', 1)
                try:  # parsing
                    b = int(b)
                except ValueError:  # can't parse
                    pass
                finally:  # add it regardless
                    invitee[a] = b
            # Append the invitee dict and append it to list of dicts
            invitees.append(invitee)
            invitee = {}

        # Making of the spreadsheet
        wb_name = f'{event_info["eventDate"]} {event_info["title"]}.xlsx'
        wb = xlsxwriter.Workbook(wb_name, {'in_memory': True})
        ws = wb.add_worksheet()
        # Cell formats - class name
        dk_cell = wb.add_format({'font_name': 'Arial', 'font_size': 10, 'bg_color': '#C41F3B', 'bold': True})
        dh_cell = wb.add_format({'font_name': 'Arial', 'font_size': 10, 'bg_color': '#A330C9', 'bold': True})
        druid_cell = wb.add_format({'font_name': 'Arial', 'font_size': 10, 'bg_color': '#FF7D0A', 'bold': True})
        hunter_cell = wb.add_format({'font_name': 'Arial', 'font_size': 10, 'bg_color': '#ABD473', 'bold': True})
        mage_cell = wb.add_format({'font_name': 'Arial', 'font_size': 10, 'bg_color': '#40C7EB', 'bold': True})
        monk_cell = wb.add_format({'font_name': 'Arial', 'font_size': 10, 'bg_color': '#00FF96', 'bold': True})
        paladin_cell = wb.add_format({'font_name': 'Arial', 'font_size': 10, 'bg_color': '#F58CBA', 'bold': True})
        priest_cell = wb.add_format({'font_name': 'Arial', 'font_size': 10, 'bg_color': '#FFFFFF', 'bold': True})
        rogue_cell = wb.add_format({'font_name': 'Arial', 'font_size': 10, 'bg_color': '#FFF569', 'bold': True})
        shaman_cell = wb.add_format({'font_name': 'Arial', 'font_size': 10, 'bg_color': '#0070DE', 'bold': True})
        warlock_cell = wb.add_format({'font_name': 'Arial', 'font_size': 10, 'bg_color': '#8787ED', 'bold': True})
        warr_cell = wb.add_format({'font_name': 'Arial', 'font_size': 10, 'bg_color': '#C79C6E', 'bold': True})
        # Cell formats - invite status
        accepted_cell = wb.add_format({'font_name': 'Arial', 'font_size': 10, 'bg_color': 'green', 'bold': True})
        standby_cell = wb.add_format({'font_name': 'Arial', 'font_size': 10, 'bg_color': 'cyan', 'bold': True})
        tentative_cell = wb.add_format({'font_name': 'Arial', 'font_size': 10, 'bg_color': 'yellow', 'bold': True})
        decline_cell = wb.add_format({'font_name': 'Arial', 'font_size': 10, 'bg_color': 'red', 'bold': True})
        # Cell Type to Cell Format translator
        cell_format = {
            'Death Knight': dk_cell,
            'Demon Hunter': dh_cell,
            'Druid': druid_cell,
            'Hunter': hunter_cell,
            'Mage': mage_cell,
            'Monk': monk_cell,
            'Paladin': paladin_cell,
            'Priest': priest_cell,
            'Rogue': rogue_cell,
            'Shaman': shaman_cell,
            'Warlock': warlock_cell,
            'Warrior': warr_cell,
            'Invited': tentative_cell,
            'Accepted': accepted_cell,
            'Declined': decline_cell,
            'Confirmed': accepted_cell,
            'Out': decline_cell,
            'Standby': standby_cell,
            'Signed Up': accepted_cell,
            'Not Signed Up': decline_cell,
            'Tentative': tentative_cell
        }
        # Widen columns in range
        ws.set_column('A:C', 20)
        # Populate the rows
        for i in range(len(invitees)):
            # Assign variables for increased readability
            invite_status = INV_TRANSLATOR[invitees[i]['inviteStatus']]
            class_name = invitees[i]['className']
            char_name = invitees[i]['name']
            # Skip all the members who have not responded (a.k.a. have the status 'Invited')
            if invite_status == 'Invited':
                continue
            # Cell value set to character's name, cell style set to character's class (class color cell BG for now only)
            ws.write(f'B{i}', char_name, cell_format[class_name])
            ws.write(f'C{i}', invite_status, cell_format[invite_status])
        # Close the sheet
        wb.close()
        # Send the file back
        await ctx.send(file=discord.File(wb_name))

    @commands.command(name='token', help='See the current token price (EU/US/KR/TW)')
    async def tok(self, ctx, region: str = 'EU'):
        region_list = ['EU', 'US', 'KR', 'TW']
        if region.upper() not in region_list:
            await ctx.send('Region {} is not supported. Try EU, US, KR or TW (not case sensitive)'.format(region))
            return
        region = region.lower()
        # Check if DB is up to date
        current_token_json = await self.db_manager.db_token['token_current'].find_one({"region": region.lower()})
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
        await ctx.send('Current **{0}** token price: **{1}g** \n_Last updated: {2} GMT+1_'
                       .format(
                            region.upper(),
                            current_token_json['price'],
                            last_updated
                       ))

    async def m_last_all(self, ctx, realm_id, realm_name):
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
            await ctx.trigger_typing()
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
            await ctx.trigger_typing()
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
