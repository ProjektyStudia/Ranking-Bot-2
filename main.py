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
bot = commands.Bot(command_prefix="$", description="Opis bota, moze dziala", intents=intents)

# stale do testowanie - potem dodac do bazy danych
NUMBER_OF_VOTES_NEEDED = 1
messages = []

print("Run bot")

# bot events
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    messages = await Database.fetch_messages_from_db()


@bot.event
async def on_message(message):
    if (len(message.embeds) > 0):
        print(message.embeds[0].title)
        if (message.embeds[0].title.startswith('Voting Battle') and message.author.id == 1030019957964161067):
            messages = await Database.insert_message_to_db(message.id, NUMBER_OF_VOTES_NEEDED)

    await bot.process_commands(message)


@bot.event
async def on_raw_reaction_add(payload):
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
        return

    # no RankingName in message
    if rankingName == "":
        data = await Database.fetch_rankings_in_guild(ctx.guild.id)

        # found one default ranking
        if (len(data) == 1):
            rankingName = data[0][0]
            rankingID = data[0][1]

        # no ranking for guild
        elif (len(data) == 0):
            # create new ranking
            rankingName = ctx.guild.name
            await Database.create_new_ranking(rankingName.replace(" ", "_"), ctx.guild.id)

            data = await Database.fetch_rankingIds(ctx.guild.id)
            rankingID = data[0][0]
            await ctx.send(f"Created your first ranking with name of server: {ctx.guild.name}.  Miau! (●'◡'●)")

        # too many ranking names, cannot pick cause no rankingName in message
        else:
            await ctx.send("In your server are several rankings, choose one and call me again! Miau! (●'◡'●)")
            return

    # RankingName in message
    else:
        data = await Database.fetch_rankingIds(ctx.guild.id, rankingName)
        if (len(data) != 1):
            await ctx.send("Invalid ranking name. If you can, correct it, pleasee~~~? ◕‿↼")
            return
        else:
            rankingID = data[0][0]


    data = await Database.fetch_user_from_points(userToDb, rankingId)
    if (len(data) == 0):
        await Database.insert_user_to_points(userToDb, rankingId)
        await Database.increase_total_memebers_in_ranking(rankingId)
        await ctx.send(f"Added {userToDb} to the {rankingName} ranking! You're welcome! Miau ＼(´ ε｀ )／")
    else:
        await ctx.send(f"User {userToDb} is already in the DB ( ͡°Ɛ ͡°)")


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
async def showRanking(ctx, rankingName: str):
    data = await Database.fetch_ranking_name(rankingName)

    #check if found any ranking with input name
    if (len(data) != 1):
        await ctx.send("Not found ranking with that name. Check typo error and try againe! Meow!")
        return

    #fetch data from ranking
    data = await Database.fetch_user_with_points(rankingName, ctx.guild.id)
    tb = pt()
    tb.title = rankingName
    tb.field_names = ["User Name", "Points"]
    for row in data:
        tb.add_row(row)
    tb.sortby = "Points"
    tb.reversesort = True
    await ctx.send(f"```\n{tb}```")

bot.run(TOKEN)