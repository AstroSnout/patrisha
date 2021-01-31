import json
import aiohttp
import motor.motor_asyncio

change_stream = None


class DBManager:
    def __init__(self, username, password, dbname):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(
            f"mongodb+srv://{username}:{password}@patrishacluster.sim1z.mongodb.net/{dbname}?retryWrites=true&w=majority"
        )
        self.server_settings = self.client['general']['settings']

        # If corrupt, new access token on https://dev.battle.net/io-docs
        # until I figure out a decent way to get one

        # self.access = cfg.BNET_ACCESS_TOKEN
        # self.token_cl = motor.motor_asyncio.AsyncIOMotorClient(cfg.DB_TOKEN)
        # self.economy_cl = motor.motor_asyncio.AsyncIOMotorClient(cfg.DB_ECONOMY)
        # self.guild_cl = motor.motor_asyncio.AsyncIOMotorClient(cfg.DB_GUILD)
        #
        # self.db_token = self.token_cl['patrisha']
        # self.db_eco = self.economy_cl['economy']
        # self.db_guild = self.guild_cl['guilds']
        #
        # self.server_settings = self.db_token['guild_settings']  # discord servers
        # self.balance = self.db_eco['balance']
        # self.apps_new = self.db_token['atb_applications']
        # self.apps_old = self.db_token['atb_processed']

    async def init_settings(self, server):
        settings = await self.server_settings.find_one({'id': server.id})
        if not settings:
            await self.server_settings.insert_one({
                'id': server.id,
                'name': server.name,
                'on_join_message': None,
                'on_leave_message': None,
                'on_join_role': None,
                'default_realm': None,
                'default_region': None,
            })

    async def get_on_join_message(self, server):
        settings = await self.server_settings.find_one({'id': server.id})
        if settings:
            return settings['on_join_message']

    async def set_on_join_message(self, server, message):
        result = await self.server_settings.update_one(
            {'id': server.id},
            {'$set':
                {
                    'on_join_message': message
                }
            }
        )
        print(result.raw_result)

    async def clear_on_join_message(self, server):
        result = await self.server_settings.update_one(
            {'id': server.id},
            {'$set':
                {
                    'on_join_message': None
                }
            }
        )
        print(result)

    async def get_on_join_role(self, server):
        settings = await self.server_settings.find_one({'id': server.id})
        if settings:
            return settings['on_join_role']

    async def set_on_join_role(self, server, role_name):
        if role_name:
            for role in server.roles:
                if role.name.lower() == role_name.lower():  # Case insensitive
                    # Found the role, update
                    result = await self.server_settings.update_one(
                        {'id': server.id},
                        {'$set':
                            {
                                'on_join_role': role_name
                            }
                        }
                    )
                    print(result)
                    return True  # Success
            return False  # Failed

    async def clear_on_join_role(self, server):
        result = await self.server_settings.update_one(
            {'id': server.id},
            {'$set':
                {
                    'on_join_role': None
                }
            }
        )
        print(result)

    async def get_default_realm(self, server):
        settings = await self.server_settings.find_one({'id': server.id})
        if settings:
            return settings['default_realm']

    async def set_default_realm(self, server, realm):
        result = await self.server_settings.update_one(
            {'id': server.id},
            {'$set':
                {
                    'default_realm': realm
                }
            }
        )
        print(result)

    async def clear_default_realm(self, server):
        result = await self.server_settings.update_one(
            {'id': server.id},
            {'$set':
                {
                    'default_realm': None
                }
            }
        )
        print(result)

    async def get_default_region(self, server):
        settings = await self.server_settings.find_one({'id': server.id})
        if settings:
            return settings['default_region']
        return

    async def set_default_region(self, server, message):
        result = await self.server_settings.update_one(
            {'id': server.id},
            {'$set':
                {
                    'default_region': message
                }
            }
        )
        print(result)

    async def clear_default_region(self, server):
        result = await self.server_settings.update_one(
            {'id': server.id},
            {'$set':
                {
                    'default_region': None
                }
            }
        )
        print(result)

    # =============================================================== #

    async def update_guild_db(self, guild_name, realm_name, members):
        # Format the guild name
        guild = '{}-{}'.format(guild_name.replace(' ', '_'), realm_name)
        # Delete the previous roster
        await self.db_guild[guild].delete_many({})
        # Add the newly requested roster
        await self.db_guild[guild].insert_many(members)
        # Tell 'em we updated
        print('Updated roster for', guild)

    async def guild_sub(self, user_id, realm_name, guild_name):
        sub = {
            "user": user_id,
            "guild": guild_name,
            "realm": realm_name
        }
        sub_in_db = await self.db_guild['guild_member_subs'].find_one(sub)
        # If he ain't there, add the user to the DB
        if not sub_in_db:
            await self.db_guild['guild_member_subs'].insert_one(sub)
            print('Added user to the database')
            return True
        # Otherwise, just inform the user that he stupid af and that he's already subbed to the guild
        else:
            return False

    async def guild_unsub(self, user_id, realm_name, guild_name):
        sub = {
            "user": user_id,
            "guild": guild_name,
            "realm": realm_name
        }
        sub_in_db = await self.db_guild['guild_member_subs'].find_one(sub)
        if not sub_in_db:
            return False
        else:
            await self.db_guild['guild_member_subs'].delete_one(sub)
            return True

    async def update_token(self, region):
        uri_list = {
            'eu': 'https://eu.api.blizzard.com/data/wow/token/?namespace=dynamic-eu&locale=en_GB&access_token=' + self.access,
            'us': 'https://us.api.blizzard.com/data/wow/token/?namespace=dynamic-us&locale=en_US&access_token=' + self.access,
            'kr': 'https://kr.api.blizzard.com/data/wow/token/?namespace=dynamic-kr&locale=ko_KR&access_token=' + self.access,
            'tw': 'https://tw.api.blizzard.com/data/wow/token/?namespace=dynamic-tw&locale=zh_TW&access_token=' + self.access
        }

        print('Getting {} token price data...'.format(region))
        # Send request
        async with aiohttp.ClientSession() as session:
            async with session.get(uri_list[region.lower()]) as token_req:
                token = json.loads(await token_req.text())
        # Make my own JSON
        my_token = {
            'region': region,
            'last_updated': token['last_updated_timestamp'],
            'price': token['price'] // 10000  # Removes obsolete silver and copper values
        }
        # Post it to DB historical
        th = await self.db_token['token_historical'].insert_one(my_token)
        # Remove outdated price
        self.db_token['token_current'].delete_one({"region": region})
        # Add the current price to the DB
        tc = await self.db_token['token_current'].insert_one(my_token)

        return my_token

    async def eco_register(self, user_id, amount):
        user = await self.db_eco['balance'].find_one({'user_id': user_id})
        if user is None:
            user = {
                'user_id': user_id,
                'balance': amount
            }
            await self.db_eco['balance'].insert_one(user)
            return True
        else:
            return False

    async def eco_add_balance(self, user_id, amount):
        user = await self.db_eco['balance'].find_one({'user_id': user_id})
        if user is None:
            return False
        else:
            await self.db_eco['balance'].delete_one(user)
            user['balance'] += amount
            await self.db_eco['balance'].insert_one(user)
            return True

    async def eco_rem_balance(self, user_id, amount):
        user = await self.db_eco['balance'].find_one({'user_id': user_id})
        if user is None:
            return False
        else:
            await self.db_eco['balance'].delete_one(user)
            user['balance'] -= amount
            await self.db_eco['balance'].insert_one(user)
            return True

    async def eco_view_balance(self, user_id):
        user = await self.db_eco['balance'].find_one({'user_id': user_id})
        if user is None:
            return None
        else:
            return user['balance']
