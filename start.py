from telethon.sync import TelegramClient

api_id = 37597265
api_hash = '650a8b45cb705150a2d3bb7f6cd41bee'
session = 'checker_01'   # change this for each account
# session = 'checker_01'   # change this for each account
# session = 'checker_02'   # change this for each account
# session = 'checker_03'   # change this for each account

client = TelegramClient(session, api_id, api_hash)
client.start()
print("Done - session saved.")
client.disconnect()