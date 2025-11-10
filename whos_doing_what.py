from groupy.client import Client
from groupy.api.bots import *
from datetime import datetime, timezone
from creds import *

client = Client.from_token(token)
group = client.groups.get(nu_chi)
bot = client.bots.list()[1].manager
rms = ""
credits_text = f"RMs: {rms} "
print(bot, bot_id, credits_text)