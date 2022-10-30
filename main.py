import asyncio
import os
import nextcord
from nextcord.ext import commands
from nextcord import Client
import logging
import sqlite3
from typing import Optional
import discord

client = Client()
# sqlite
connection = sqlite3.connect("cham.db")
cursor = connection.cursor()


# consts

TOKEN = 'MTAzMDAxOTk1Nzk2NDE2MTA2Nw.G5fBCm.IpGo8olJI7RuRnTI7EfFE_qVbRwYdZdrBNr5hY'
GUILD_ID = 'Ranking Chamów'


# logger
logger = logging.getLogger('nextcord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(
    filename='nextcord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# intents
intents = nextcord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.messages = True
intents.reactions = True

# bot
bot = commands.Bot(command_prefix="$",
                   description="Opis bota, moze dziala", intents=intents)

# stale do testowanie - potem dodac do bazy danych

messages = []


# bot events
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


@bot.event
async def on_message(message):
    if (len(message.embeds) > 0):
        if (message.embeds[0].title.startswith('(Nazwa Tabeli)') and message.author.id == 1030019957964161067):
            messages.append(message.id)

    await bot.process_commands(message)


@bot.event
async def on_raw_reaction_add(payload):
    if (payload.message_id in messages):
        if (payload.emoji.name == '👍'):
            channel = bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            embed = message.embeds[0]
            embed.set_field_at(
                1, name=embed.fields[1].name, value=int(embed.fields[1].value) - 1)
            embed.set_footer(text="Zaakceptowano")
            await message.edit(embed=embed)
            await message.clear_reactions()

        if (payload.emoji.name == '👎'):
            channel = bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            embed = message.embeds[0]
            embed.set_field_at(
                2, name=embed.fields[2].name, value=int(embed.fields[2].value) - 1)
            embed.set_footer(text="Zaakceptowano")
            await message.edit(embed=embed)
            await message.clear_reactions()

            # mozna zostawic zeby czyscilo reakcje, ale trzeba bedzie zrobic zeby user nie mogl dodawac reakci ponownie

# bot commands


@ bot.command()
async def ping(ctx):
    await ctx.send("Pong")


@ bot.command()
async def joined(ctx, member: nextcord.Member):
    """Says when a member joined."""
    await ctx.send(f"{member.name} joined in {member.joined_at}")


@ bot.command(description="My first slash command")
async def hello(ctx: nextcord.Interaction):
    await ctx.send("Hello!")


@ bot.command(description="Shows bot's latency", guild_ids=[GUILD_ID])
async def latency(ctx: nextcord.Integration):
    await ctx.send(f"The bot latency is {round(bot.latency * 1000)}ms.")


@ bot.command()
async def members(ctx):
    names = [x.name for x in ctx.guild.members]
    await ctx.send(names)


@ bot.command()
async def addPerson(ctx, *args):
    # args are optional, [0] - mention user, [1] - ranking name
    # async def addPerson(ctx, person: Optional[nextcord.Member], rankingName: Optional[str]):
    rankingID = -1
    userToDb = ""
    rankingName = ""
    match len(args):
        case 2:
            userToDb = args[0]
            rankingName = args[1]
        case 1:
            userToDb = args[0]
        case 0:
            userToDb = ctx.author.mention
        case _:
            await ctx.send("Too many arguments.  Miau! (●'◡'●) \n Remember: ranking name has no whitespaces!")
            return

    # check if custom name or authorName is a mention
    if (not (userToDb.startsWith("<@") and userToDb.endsWith(">"))):
        return
    # no RankingName in message
    if rankingName == "":
        cursor.execute(
            f"""SELECT RankingName, RankingID from Rankings WHERE GuildID='{ctx.guild.id}'""")
        data = cursor.fetchall()

        # found one default ranking
        if (len(data) == 1):
            rankingName = data[0][0]
            rankingID = data[0][1]

        # no ranking for guild
        elif (len(data) == 0):
            # create new ranking
            cursor.execute(
                f"""INSERT INTO Rankings (RankingName, GuildID) VALUES ('{ctx.guild.name.replace(" ", "_")}','{ctx.guild.id}')""")
            connection.commit()

            rankingName = ctx.guild.name
            cursor.execute(
                f"""SELECT RankingID from Rankings WHERE GuildID='{ctx.guild.id}'""")
            data = cursor.fetchall()
            rankingID = data[0][0]
            await ctx.send(f"Created your first ranking with name of server: {ctx.guild.name}.  Miau! (●'◡'●)")

        # too many ranking names, cannot pick cause no rankingName in message
        else:
            await ctx.send("In your server are several rankings, choose one and call me again! Miau! (●'◡'●)")
            return

    # RankingName in message
    else:
        cursor.execute(
            f"""SELECT RankingID from Rankings WHERE GuildID='{ctx.guild.id}' AND RankingName='{rankingName}'""")
        data = cursor.fetchall()
        if (len(data) != 1):
            await ctx.send("Invalid ranking name. If you can, correct it, pleasee~~~? ◕‿↼")
            return
        else:
            rankingID = data[0][0]

    cursor.execute(
        f"""SELECT User from Points WHERE User='{userToDb}' AND RankingID='{rankingID}'""")
    data = cursor.fetchall()
    if (len(data) == 0):
        cursor.execute(
            f"""INSERT INTO Points VALUES('{userToDb}', {rankingID} , {int("0")})""")
        connection.commit()
        await ctx.send(f"Added {userToDb} to the {rankingName} ranking! You're welcome! Miau ＼(´ ε｀ )／")
    else:
        await ctx.send(f"User {userToDb} is already in the DB")


@ bot.command()
async def showTable(ctx):
    for row in cursor.execute("SELECT osoba, punkty from lista_chamow"):
        await ctx.send(row)


@ bot.command()
async def addPoint(ctx, person: str, description: str):
    print("Add point")
    cursor.execute(f"""UPDATE lista_chamow
    SET punkty = punkty + 1
    WHERE osoba = '{person}'
""")
    connection.commit()
    embed = discord.Embed(
        title="(Nazwa Tabeli), Bitwa o punkt!", color=0x01ffbf)
    embed.add_field(
        name=f"Użytkownik {ctx.author} chce dodac punkta użytkownikowi {person}", value=f"{description}", inline=False)
    embed.add_field(name="Daj reakcje 👍 jeśli się zgadzasz, pozostało:",
                    value=2, inline=True)
    embed.add_field(
        name="Daj reakcje 👎 jeśli się nie zgadzasz, pozostało:", value=2, inline=True)
    embed.set_footer(text="#Bot Rankingowy")

    await ctx.send(embed=embed)


bot.run(TOKEN)

connection.close()
