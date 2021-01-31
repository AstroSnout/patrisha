import motor.motor_asyncio

change_stream = None


class DBManager:
    def __init__(self, username, password, dbname):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(
            f"mongodb+srv://{username}:{password}@patrishacluster.sim1z.mongodb.net/{dbname}?retryWrites=true&w=majority"
        )
        self.server_settings = self.client['general']['settings']

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
