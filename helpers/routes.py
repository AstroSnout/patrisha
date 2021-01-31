from helpers import util
import configparser


class BlizzardRoutes:
    settings = configparser.ConfigParser()
    settings.read('./settings.ini')
    token = settings['blizzard']['client_secret']
    api_key = settings['blizzard']['api_key']

    @staticmethod
    def realm(realm):
        return 'https://eu.api.battle.net/data/wow/realm/{0}?namespace=dynamic-eu&locale=en_GB&access_token={1}'\
            .format(
                realm,
                BlizzardRoutes.token
            )

    @staticmethod
    def dungeons(realm_id):
        return 'https://eu.api.battle.net/data/wow/connected-realm/{0}/mythic-leaderboard/?namespace=dynamic-eu&locale=en_GB&access_token={1}'\
            .format(
                realm_id,
                BlizzardRoutes.token
            )


class RaiderIORoutes():
    def __init__(self):
        pass

    @staticmethod
    def affixes(region='eu'):
        return 'https://raider.io/api/v1/mythic-plus/affixes?region={}&locale=en'.format(region)

    @staticmethod
    def mythic_score(character_name, realm, region='eu'):
        return 'https://raider.io/api/v1/characters/profile?region={0}&realm={1}&name={2}&fields=mythic_plus_scores'\
            .format(
                region,
                realm,
                character_name
            )

    @staticmethod
    def character_profile(character_name, realm, region='eu'):
        return 'https://raider.io/api/v1/characters/profile?region={0}&realm={1}&name={2}&fields=mythic_plus_best_runs'\
            .format(
                region,
                realm,
                character_name
            )

    @staticmethod
    def recent_runs(character_name, realm, region='eu'):
        return 'https://raider.io/api/v1/characters/profile?region={0}&realm={1}&name={2}&fields=mythic_plus_recent_runs'\
            .format(
                region,
                realm,
                character_name
            )

    @staticmethod
    def all_character_data(character_name, realm, region='eu'):
        return 'https://raider.io/api/v1/characters/profile?region={0}&realm={1}&name={2}&fields=gear%2Cmythic_plus_scores%2Cmythic_plus_recent_runs'\
            .format(
                region,
                realm,
                character_name
            )
