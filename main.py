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
from Database.db import Database
from Helpers.helper import Helper

client = Client()

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
NUMBER_OF_VOTES_NEEDED = 1
messages = []

print("Run bot")

# bot events


@bot.event
async def on_ready():
    global messages
    print(f'We have logged in as {bot.user}')
    messages = await Database.fetch_messages_from_db()


@bot.event
async def on_message(message):
    global messages
    if (len(message.embeds) > 0):
        print(message.embeds[0].title)
        if (message.embeds[0].title.startswith('Voting Battle') and message.author.id == 1030019957964161067):
            messages = await Database.insert_message_to_db(message.id, NUMBER_OF_VOTES_NEEDED)

    await bot.process_commands(message)


@bot.event
async def on_raw_reaction_add(payload):
    global messages
    print(messages)
    for m in messages:
        if (int(payload.message_id) == int(m[0]) and not payload.member.bot):
            if (payload.emoji.name == '👍'):
                channel = bot.get_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)
                print(message)

                # get points and user mention
                number_of_points_to_add = message.embeds[0].fields[0].name.split(' ')[
                    4]
                person_that_gets_points = Helper.find_user_by_string_name(message.embeds[0].fields[0].name.split(' ')[
                    7], bot).mention

                # calculate number of reactions on message
                number_of_reactions = 0
                for reaction in message.reactions:
                    if reaction.emoji == '👍':
                        number_of_reactions = reaction.count - 1

                embed = message.embeds[0]
                votes_after_update = await Database.update_message_votes(payload.message_id,
                                                                         "Agreed", "Add", number_of_reactions)

                if (votes_after_update == (NUMBER_OF_VOTES_NEEDED)):
                    embed.set_footer(
                        text="Voting ended, result: Agreed")
                    embed.color = discord.Color.green()
                    print("Voting ended, points added")
                    await Database.delete_message_from_db(payload.message_id)
                    messages = await Database.change_user_points(person_that_gets_points, number_of_points_to_add)

                embed.set_field_at(
                    1, name=embed.fields[1].name, value=int(NUMBER_OF_VOTES_NEEDED - number_of_reactions))

                await message.edit(embed=embed)

            if (payload.emoji.name == '👎'):
                channel = bot.get_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)

                # get points and user mention
                number_of_points_to_add = message.embeds[0].fields[0].name.split(' ')[
                    4]
                person_that_gets_points = Helper.find_user_by_string_name(message.embeds[0].fields[0].name.split(' ')[
                    7], bot).mention

                number_of_reactions = 0
                for reaction in message.reactions:
                    if reaction.emoji == '👎':
                        number_of_reactions = reaction.count - 1

                embed = message.embeds[0]
                votes_after_update = await Database.update_message_votes(payload.message_id,
                                                                         "Rejected", "Remove", number_of_reactions)

                if (votes_after_update == (NUMBER_OF_VOTES_NEEDED)):
                    embed.set_footer(
                        text="Voting ended, result: Rejected")
                    embed.color = discord.Color.red()
                    print("Voting ended, result: Rejected")
                    messages = await Database.delete_message_from_db(payload.message_id)

                embed.set_field_at(
                    2, name=embed.fields[2].name, value=int(NUMBER_OF_VOTES_NEEDED - number_of_reactions))

                await message.edit(embed=embed)


@bot.event
async def on_raw_reaction_remove(payload):
    global messages
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
                await Database.update_message_votes(payload.message_id,
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
                await Database.update_message_votes(payload.message_id,
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
        await ctx.send("Invalid user, pleeesa use user mentions only!  Miau! (●'◡'●)")
        return

    # no RankingName in message
    if rankingName == "":
        data = Database.fetch_rankings_in_guild(ctx.guild.id)

        # found one default ranking
        if (len(data) == 1):
            rankingName = data[0][0]
            rankingID = data[0][1]

        # no ranking for guild
        elif (len(data) == 0):
            # create new ranking
            rankingName = ctx.guild.name
            Database.create_new_ranking(
                rankingName.replace(" ", "_"), ctx.guild.id)

            data = Database.fetch_rankingIds(ctx.guild.id)
            rankingID = data[0][0]
            await ctx.send(f"Created your first ranking with name of server: {ctx.guild.name}.  Miau! (●'◡'●)")

        # too many ranking names, cannot pick cause no rankingName in message
        else:
            await ctx.send("In your server are several rankings, choose one and call me again! Miau! (●'◡'●)")
            return

    # RankingName in message
    else:
        data = Database.fetch_rankingIds(ctx.guild.id, rankingName)
        if (len(data) != 1):
            await ctx.send("Invalid ranking name. If you can, correct it, pleasee~~~? ◕‿↼")
            return
        else:
            rankingID = data[0][0]

    data = Database.fetch_user_from_points(userToDb, rankingID)
    if (len(data) == 0):
        Database.insert_user_to_points(userToDb, rankingID)
        Database.increase_total_memebers_in_ranking(rankingID)
        await ctx.send(f"Added {userToDb} to the {rankingName} ranking! You're welcome! Miau ＼(´ ε｀ )／")
    else:
        await ctx.send(f"User {userToDb} is already in the DB ( ͡°Ɛ ͡°)")


@ bot.command()
async def removePerson(ctx, *args):
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
        await ctx.send("Invalid user, pleeesa use user mentions only!  Miau! (●'◡'●)")
        return

    # no RankingName in message
    if rankingName == "":
        data = Database.fetch_rankings_in_guild(ctx.guild.id)

        # found one default ranking
        if (len(data) == 1):
            rankingName = data[0][0]
            rankingID = data[0][1]

        # too many ranking names, cannot pick cause no rankingName in message
        else:
            await ctx.send("In your server are several rankings, choose one and call me again! Miau! (●'◡'●)")
            return

    # RankingName in message
    else:
        data = Database.fetch_rankingIds(ctx.guild.id, rankingName)
        if (len(data) != 1):
            await ctx.send("Invalid ranking name. If you can, correct it, pleasee~~~? ◕‿↼")
            return
        else:
            rankingID = data[0][0]

    user = Database.fetch_user_from_points(userToDb, rankingID)
    if (len(user) == 0):
        await ctx.send(f"User {userToDb} is not in the {rankingName} ranking ( ͡°Ɛ ͡°)")
        return
    else:
        Database.decrease_total_memebers_in_ranking(rankingID)
        Database.remove_user_from_points(userToDb, rankingID)
        await ctx.send(f"Removed {userToDb} from the {rankingName} ranking :( We will miss You! Miau ＼(´ ε｀ )／")
        return


@bot.command()
async def createRanking(ctx, rankingName: str):
    if (rankingName == ""):
        await ctx.send("Invalid ranking name. If you can, correct it, pleasee~~~? ◕‿↼")
        return
    Database.create_new_ranking(
        rankingName.replace(" ", "_"), ctx.guild.id)


@ bot.command()
async def vote(ctx, person: str, description: str, points: int, *args):
    # args are optional, [0] - ranking name
    if (len(args) > 1):
        await ctx.send("Too many arguments.  Miau! (●'◡'●)")
        return

    if (len(args) == 0):
        print("No ranking name")
        data = Database.fetch_rankings_in_guild(ctx.guild.id)

        if (len(data) == 1):
            rankingId = data[0][1]
        else:
            await ctx.send("In your server are several rankings, choose one and call me again! Miau! (●'◡'●)")
            return

    if (len(args) == 1):
        rankingName = args[0]
        ranking = Database.fetch_rankingIds(ctx.guild.id, rankingName)
        if (len(ranking) != 1):
            await ctx.send("Invalid ranking name. If you can, correct it, pleasee~~~? ◕‿↼")
            return

        rankingId = ranking[0][0]

    nickname = ""
    for x in ctx.guild.members:
        if (x.mention == person):
            nickname = x.name
            break

    if (nickname == ""):
        await ctx.send("Invalid user, pleeesa use user mentions only!  Miau! (●'◡'●)")
        return
    users = Database.fetch_users_from_ranking(rankingId)
    user = Helper.find_user_by_string_name(nickname, bot)
    if (user.mention not in users[0]):
        await ctx.send("User is not in the ranking. Miau! (●'◡'●)")
        return

    if (points == 0):
        await ctx.send(f"Voting for 0 points, are u silly? Meow (◕‿◕✿)")
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
async def showRanking(ctx, *args):
    if (len(args) == 0):

        rankings = Database.fetch_rankings_in_guild(ctx.guild.id)

        # found one default ranking
        if (len(rankings) == 1):
            rankingName = rankings[0][0]
        else:
            await ctx.send("Too few arguments.  Miau! (●'◡'●) \n Remember: ranking name has no whitespaces!")
            return
    else:
        rankingName = args[0]

    # fetch data from ranking
    data = Database.fetch_user_with_points(rankingName, ctx.guild.id)
    tb = pt()
    tb.title = rankingName
    tb.field_names = ["User Name", "Points"]
    for row in data:
        print(row)
        mention = row[0]
        user = Helper.find_user_by_mention(mention, bot)
        if (user != None):
            _row = [user.name, row[1]]
            tb.add_row(_row)
    tb.sortby = "Points"
    tb.reversesort = True
    await ctx.send(f"```\n{tb}```")

bot.run(TOKEN)
