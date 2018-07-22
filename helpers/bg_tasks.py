import discord
from discord.ext import commands

from helpers import util
from helpers.db_manager import DBManager


# For Guild subcategory in game_wow.py
async def guild_sub_sending(bot):
    db_manager = DBManager()
    # Retrieve all members from DB and put them in a list
    subs = [doc async for doc in db_manager.db_guild['guild_member_subs'].find({})]
    update_these = []
    for sub in subs:
        # Vars for easier typing
        guild_name = sub['guild']
        realm_name = sub['realm']
        user = bot.get_user(sub['user'])  # Gets discord.User via user ID

        # Retrieve current members of a specified guild from Blizzard API
        current_guild_roster_full = await util.get_guild_roster(realm_name, guild_name)
        # String formatting for searching the collection in the DB
        guild_for_db = '{}-{}'.format(guild_name.replace(' ', '_'), realm_name)
        last_guild_roster = [doc async for doc in db_manager.db_guild[guild_for_db].find({})]
        # Turn those roster JSON files into a list of character names, 'cause I'm lazy to do it elegantly
        current_guild_roster = [member['character']['name'] for member in current_guild_roster_full]
        last_guild_roster = [member['character']['name'] for member in last_guild_roster]
        # Compare the current roster with the one saved in the DB and assert who left/joined
        members_left = [member for member in last_guild_roster if member not in current_guild_roster]
        members_joined = [member for member in current_guild_roster if member not in last_guild_roster]
        # Print them fellas that left/got kicked
        if members_left:
            print('A player left the guild')
            # Adding to the list 'cause we want to update after we've sent the info to all the users
            if (realm_name, guild_name) not in update_these:
                update_these.append((realm_name, guild_name))
            # Not sure why I have this try block here
            try:
                await user.send('Members that left {}: {}'.format(guild_name.title(), ' '.join(members_left)))
            except:
                print('An error has occured in guild sending loop (excpt1)')
        # Print fellas that joined
        if members_joined:
            print('A player joined the guild')
            # Adding to the list 'cause we want to update after we've sent the info to all the users
            if (realm_name, guild_name) not in update_these:
                update_these.append((realm_name, guild_name))
            # Not sure why I have this try block here
            try:
                await user.send('Members that joined {}: {}'.format(guild_name.title(), ' '.join(members_joined)))
            except:
                print('An error has occured in guild sending loop (excpt2)')
    # Update the DB
    if update_these:
        for sub in update_these:
            guild_name = sub[1]
            realm_name = sub[0]
            current_guild_roster_full = await util.get_guild_roster(realm_name, guild_name)
            await db_manager.update_guild_db(guild_name, realm_name, current_guild_roster_full)
