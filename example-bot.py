import os
import nextcord
from nextcord.ext import commands
import logging
import sqlite3


#sqlite
connection = sqlite3.connect("cham.db")
cursor = connection.cursor()


#consts
GUILD_ID = os.getenv('DISCORD_GUILD')

#logger
logger = logging.getLogger('nextcord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='nextcord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

#intents
intents = nextcord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True

#bot
bot = commands.Bot(command_prefix="$", description="Opis bota, moze dziala", intents=intents)


#bot commands
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.command()
async def add(ctx, left: int, right: int):
    """Adds two numbers together."""
    await ctx.send(left + right)

@bot.command()
async def ping(ctx):
    await ctx.send("Pong ty kurwo")    

@bot.command()
async def joined(ctx, member: nextcord.Member):
    """Says when a member joined."""
    await ctx.send(f"{member.name} joined in {member.joined_at}")    

@bot.command(description="My first slash command")
async def hello(ctx: nextcord.Interaction):
    await ctx.send("Hello!")

@bot.command(description="Shows bot's latency", guild_ids=[GUILD_ID])
async def latency(ctx:nextcord.Integration):
    await ctx.send(f"The bot latency is {round(bot.latency * 1000)}ms.")

@bot.command()
async def members(ctx):
    names = [x.name for x in ctx.guild.members]
    await ctx.send(names)

@bot.command()
async def addPerson(ctx, person: str):
    cursor.execute(f"""
    INSERT INTO lista_chamow VALUES
        ('{person}', {int("0")})
""")
    connection.commit()
    await ctx.send(f"Added {person} to the DB (mayyyyyyyyybe :D)")

@bot.command()
async def showTable(ctx):
    for row in cursor.execute("SELECT osoba, punkty from lista_chamow"):
        await ctx.send(row)  

@bot.command()
async def addPoint(ctx, person:str):
    cursor.execute(f"""UPDATE lista_chamow
    SET punkty = punkty + 1 
    WHERE osoba = '{person}'
""")
    connection.commit()
    await ctx.send(f"Added one point to {person}")  



bot.run('MTAzMDAxOTk1Nzk2NDE2MTA2Nw.G5fBCm.IpGo8olJI7RuRnTI7EfFE_qVbRwYdZdrBNr5hY')

connection.close()