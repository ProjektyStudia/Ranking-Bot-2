from prettytable import PrettyTable as pt
import asyncio
import os
import nextcord
from nextcord.ext import commands
from nextcord import Client
import logging
import sqlite3
from typing import Optional
import discord
from dotenv import load_dotenv

client = Client()

# sqlite
# sqlite
connection = sqlite3.connect("cham.db")
cursor = connection.cursor()


# consts

if load_dotenv():

    TOKEN = os.getenv('TOKEN')
else:
    TOKEN = os.environ["TOKEN"]


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
NUMBER_OF_VOTES_NEEDED = 2
messages = []

print("start")

# helper functions


def find_user_by_string_name(name: str):
    for user in bot.get_all_members():
        if user.name == name:
            return user
    return None


async def fetch_messages_from_db():
    print("Started fetching data from db")
    cursor.execute(
        f"""SELECT Message_id, Agreed, Rejected, NeedTotalVotes FROM Messages""")
    data = cursor.fetchall()
    messages.clear()  # clear list
    for record in data:
        messages.append(record)

    print("Finished fetching")


async def insert_message_to_db(message_id, needVotes):
    cursor.execute(
        f"""INSERT INTO Messages (Message_id, Agreed, Rejected, NeedTotalVotes) VALUES('{message_id}', 0, 0, {needVotes});""")
    connection.commit()
    await fetch_messages_from_db()


async def update_message_votes(message_id, vote_type, action, vote_count):
    if action == "Add":
        cursor.execute(
            f"""UPDATE Messages SET {vote_type} = {vote_count} where Message_id = '{message_id}';""")
    elif action == "Remove":
        cursor.execute(
            f"""UPDATE Messages SET {vote_type} = {vote_count} where Message_id = '{message_id}';""")
    else:
        return
    connection.commit()
    await fetch_messages_from_db()
    return vote_count


async def delete_message_from_db(message_id):
    cursor.execute(
        f"""DELETE FROM Messages where Message_id = '{message_id}';""")
    connection.commit()
    await fetch_messages_from_db()


async def change_user_points(user_id, points):
    cursor.execute(
        f"""UPDATE Points SET Points = Points + {points} where User = '{user_id}';""")
    connection.commit()
    await fetch_messages_from_db()

# bot events


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    await fetch_messages_from_db()


@bot.event
async def on_message(message):
    if (len(message.embeds) > 0):
        print(message.embeds[0].title)
        if (message.embeds[0].title.startswith('Voting Battle') and message.author.id == 1030019957964161067):
            await insert_message_to_db(message.id, NUMBER_OF_VOTES_NEEDED)
            await fetch_messages_from_db()

    await bot.process_commands(message)


@bot.event
async def on_raw_reaction_add(payload):
    for m in messages:
        if (int(payload.message_id) == int(m[0]) and not payload.member.bot):
            if (payload.emoji.name == '👍'):
                channel = bot.get_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)

                # get points and user mention
                number_of_points_to_add = message.embeds[0].fields[0].name.split(' ')[
                    4]
                person_that_gets_points = find_user_by_string_name(message.embeds[0].fields[0].name.split(' ')[
                    7]).mention

                # calculate number of reactions on message
                number_of_reactions = 0
                for reaction in message.reactions:
                    if reaction.emoji == '👍':
                        number_of_reactions = reaction.count - 1

                embed = message.embeds[0]
                votes_after_update = await update_message_votes(payload.message_id,
                                                                "Agreed", "Add", number_of_reactions)

                if (votes_after_update == (NUMBER_OF_VOTES_NEEDED)):
                    embed.set_footer(
                        text="Voting ended, result: Agreed")
                    embed.color = discord.Color.green()

                    print("Voting ended, points added")
                    await delete_message_from_db(payload.message_id)
                    await change_user_points(person_that_gets_points, number_of_points_to_add)

                embed.set_field_at(
                    1, name=embed.fields[1].name, value=int(NUMBER_OF_VOTES_NEEDED - number_of_reactions))

                await message.edit(embed=embed)

            if (payload.emoji.name == '👎'):
                channel = bot.get_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)

                # get points and user mention
                number_of_points_to_add = message.embeds[0].fields[0].name.split(' ')[
                    4]
                person_that_gets_points = find_user_by_string_name(message.embeds[0].fields[0].name.split(' ')[
                    7]).mention

                number_of_reactions = 0
                for reaction in message.reactions:
                    if reaction.emoji == '👎':
                        number_of_reactions = reaction.count - 1

                embed = message.embeds[0]
                votes_after_update = await update_message_votes(payload.message_id,
                                                                "Rejected", "Remove", number_of_reactions)

                if (votes_after_update == (NUMBER_OF_VOTES_NEEDED)):
                    embed.set_footer(
                        text="Voting ended, result: Rejected")
                    embed.color = discord.Color.red()
                    print("Voting ended, result: Rejected")
                    await delete_message_from_db(payload.message_id)

                embed.set_field_at(
                    2, name=embed.fields[2].name, value=int(NUMBER_OF_VOTES_NEEDED - number_of_reactions))

                await message.edit(embed=embed)


@bot.event
async def on_raw_reaction_remove(payload):
    for m in messages:
        if (int(payload.message_id) == int(m[0])):
            if (payload.emoji.name == '👍'):
                channel = bot.get_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)

                number_of_reactions = 0
                for reaction in message.reactions:
                    if reaction.emoji == '👍':
                        number_of_reactions = reaction.count - 1

                embed = message.embeds[0]
                await update_message_votes(payload.message_id,
                                           "Agreed", "Add", number_of_reactions)

                embed.set_field_at(
                    1, name=embed.fields[1].name, value=int(NUMBER_OF_VOTES_NEEDED - number_of_reactions))

                await message.edit(embed=embed)

            if (payload.emoji.name == '👎'):
                channel = bot.get_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)

                number_of_reactions = 0
                for reaction in message.reactions:
                    if reaction.emoji == '👎':
                        number_of_reactions = reaction.count - 1

                embed = message.embeds[0]
                await update_message_votes(payload.message_id,
                                           "Rejected", "Remove", number_of_reactions)

                embed.set_field_at(
                    2, name=embed.fields[2].name, value=int(NUMBER_OF_VOTES_NEEDED - number_of_reactions))

                await message.edit(embed=embed)


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


# @ bot.command(description="Shows bot's latency", guild_ids=[GUILD_ID])
# async def latency(ctx: nextcord.Integration):
#     await ctx.send(f"The bot latency is {round(bot.latency * 1000)}ms.")


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

    if (len(args) == 0):
        userToDb = ctx.author.mention
    elif (len(args) == 1):
        userToDb = args[0]
    elif (len(args) == 2):
        userToDb = args[0]
        rankingName = args[1]
    else:
        await ctx.send("Too many arguments.  Miau! (●'◡'●) \n Remember: ranking name has no whitespaces!")

    # check if custom name or authorName is a mention
    if (not (userToDb.startswith("<@") and userToDb.endswith(">"))):
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
        cursor.execute(
            f"""UPDATE Rankings SET NumberOfMembers = NumberOfMembers + 1 where RankingID = {rankingID};""")  # update number of members in ranking
        connection.commit()
        await ctx.send(f"Added {userToDb} to the {rankingName} ranking! You're welcome! Miau ＼(´ ε｀ )／")
    else:
        await ctx.send(f"User {userToDb} is already in the DB")


@ bot.command()
async def showTable(ctx):
    for row in cursor.execute("SELECT osoba, punkty from lista_chamow"):
        await ctx.send(row)


@ bot.command()
async def vote(ctx, person: str, description: str, points: int):

    nickname = ""
    for x in ctx.guild.members:
        if (x.mention == person):
            nickname = x.name
            break

    if (points == 0):
        await ctx.send(f"Voting for 0 points, are u silly? Meow (ﾉ≧ڡ≦)")
        return

    print("Started voting")
    embed = discord.Embed(
        title="Voting Battle in (Nazwa Tabeli)", color=0xffff00)
    if (points > 0):
        embed.add_field(
            name=f"{ctx.author.name} wants to add {points} point(s) to {nickname} because:", value=f"{description}", inline=False)
    if (points < 0):
        embed.add_field(
            name=f"{ctx.author.name} wants to remove {points} point(s) from {nickname} because:", value=f"{description}", inline=False)
    embed.add_field(name="Approve voting by reacting 👍, votes left:",
                    value=NUMBER_OF_VOTES_NEEDED, inline=True)
    embed.add_field(
        name="To reject react 👎, votes left:", value=NUMBER_OF_VOTES_NEEDED, inline=True)
    embed.set_footer(text="#Rankuś ＼(´ ε｀ )／")
    message = await ctx.send(embed=embed)
    await message.add_reaction("👍")
    await message.add_reaction("👎")


@bot.command()
async def showRanking(ctx, rankingName: str):
    cursor.execute(
        f"""SELECT RankingName from Rankings WHERE RankingName='{rankingName}'""")
    data = cursor.fetchall()
    if (len(data) != 1):
        await ctx.send("Not found ranking with that name. Check typo error and try againe! Meow!")
        return

    cursor.execute(
        f"""SELECT p.User, p.Points from Points p INNER JOIN Rankings r ON r.RankingID = p.RankingID WHERE r.RankingName='{rankingName}'""")
    data = cursor.fetchall()
    tb = pt()
    tb.title = rankingName
    tb.field_names = ["User Name", "Points"]
    for row in data:
        tb.add_row(row)
    tb.sortby = "Points"
    tb.reversesort = True
    await ctx.send(f"```\n{tb}```")

bot.run(TOKEN)

connection.close()
