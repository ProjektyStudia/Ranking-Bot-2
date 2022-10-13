#it's second way to connect bot, we won't use it
#instead we will use bot.py

# import os
# import random

# import discord
# intents = discord.Intents.default()
# intents.messages = True
# intents.message_content  = True
# from dotenv import load_dotenv

# load_dotenv()
# TOKEN = os.getenv('DISCORD_TOKEN')
# GUILD = os.getenv('DISCORD_GUILD')

# client = discord.Client(intents=intents)

# @client.event
# async def on_ready():
#     guild = discord.utils.find(lambda g: g.name == GUILD, client.guilds)
#     print(
#         f'{client.user} is connected to the following guild:\n'
#         f'{guild.name}(id: {guild.id})'
#     )

# @client.event
# async def on_message(message):
#     if message.author == client.user:
#         return

#     brooklyn_99_quotes = [
#         'I\'m the human form of the 💯 emoji.',
#         'Bingpot!',
#         (
#             'Cool. Cool cool cool cool cool cool cool, '
#             'no doubt no doubt no doubt no doubt.'
#         ),
#     ]

#     print("Received a message:", message.content)

#     if message.content == '99!':
#         response = random.choice(brooklyn_99_quotes)
#         await message.channel.send(response)

#     if message.content == "ping":
#         await message.channel.send('pong')

# client.run(TOKEN)