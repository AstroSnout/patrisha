import requests
import json


BOT_TOKEN = 'NDA5MDg3MTQ2MjgxMTQwMjM0.DVZfrw.WmSJIM_c-NCNB0QlcYekWlpo_QE'
BNET_API_KEY = '62bb52a80e164bbc845f639865a91f57'
BNET_API_SECRET = 'aWlJzDHA4Y2qcdzP2fZDHyFKPwTb2Pqv'

access_token_grant = f'https://eu.battle.net/oauth/token?grant_type=client_credentials&client_id={BNET_API_KEY}&client_secret={BNET_API_SECRET}'
print(requests.get(access_token_grant).content)
BNET_ACCESS_TOKEN = json.loads(
    requests.get(access_token_grant).content
)['access_token']

DB_TOKEN = "mongodb://trishma:baza123@ds157528.mlab.com:57528/patrisha"
DB_ECONOMY = "mongodb://trishma:baza123@ds229380.mlab.com:29380/economy"
DB_GUILD = "mongodb://trishma:baza123@ds119988.mlab.com:19988/guilds"