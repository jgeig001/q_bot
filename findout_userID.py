import telepot

TOKEN = 'INSERT_YOUR_TOKEN_HERE_AND_HIT_RUN'
bot = telepot.Bot(TOKEN)
# send a message to the running bot
user_id = bot.getUpdates()[0]['message']['from']['id']
print(f"user_id {user_id}")
