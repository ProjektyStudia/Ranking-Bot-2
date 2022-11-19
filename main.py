from prettytable import PrettyTable as pt
import asyncio
import os
import nextcord
from nextcord.ext import commands
from nextcord import Client, Intents, Interaction, SlashOption
import logging
import sqlite3
from typing import Optional
import discord
from dotenv import load_dotenv
from Database.db import Database
from Helpers.helper import Helper

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

intents = Intents.default()
intents.message_content = True
intents.members = True
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
        if (message.embeds[0].title.startswith('Voting Battle') and message.author.id == 1030019957964161067):
            messages = await Database.insert_message_to_db(message.id, NUMBER_OF_VOTES_NEEDED)

    await bot.process_commands(message)


@bot.event
async def on_raw_reaction_add(payload):
    global messages
    for m in messages:
        if (int(payload.message_id) == int(m[0]) and not payload.member.bot):
            if (payload.emoji.name == '👍'):
                channel = bot.get_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)

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

# @ bot.command(description="Shows bot's latency", guild_ids=[GUILD_ID])
# async def latency(ctx: nextcord.Integration):
#     await ctx.send(f"The bot latency is {round(bot.latency * 1000)}ms.")


@ bot.command()
async def members(ctx):
    names = [x.name for x in ctx.guild.members]
    await ctx.send(names)

# @ bot.command()
# async def addPerson(ctx, *args):
#     # args are optional, [0] - mention user, [1] - ranking name
#     # async def addPerson(ctx, person: Optional[nextcord.Member], rankingName: Optional[str]):
#     rankingID = -1
#     userToDb = ""
#     rankingName = ""

#     if (len(args) == 0):
#         userToDb = ctx.author.mention
#     elif (len(args) == 1):
#         userToDb = args[0]
#     elif (len(args) == 2):
#         userToDb = args[0]
#         rankingName = args[1]
#     else:
#         await ctx.send("Too many arguments.  Miau! (●'◡'●) \n Remember: ranking name has no whitespaces!")

@bot.slash_command(guild_ids=[1030024780314845234])
async def add_to_ranking(interaction: Interaction, user:Optional[str], ranking_name: Optional[str]):
    """Adding member to ranking.

    Parameters
    ----------
    interaction: Interaction
        The interaction object
    user: Optional[str]
        Mention user or let it blank to add yourself
    ranking_name: Optional[str]
        Type ranking name to which you want to add someone or leave blank if only 1 ranking exist
    """
    rankingID = -1
    if user is None:
        user = interaction.user.mention
    # check if custom name or authorName is a mention
    if (not (user.startswith("<@") and user.endswith(">"))):
        await interaction.response.send_message("Invalid user, pleeesa use user mentions only!  Miau! (●'◡'●)")
        return

    # no RankingName in message
    if ranking_name is None:
        data = Database.fetch_rankings_in_guild(interaction.guild.id)

        # found one default ranking
        if (len(data) == 1):
            ranking_name = data[0][0]
            rankingID = data[0][1]

        # no ranking for guild
        elif (len(data) == 0):
            # create new ranking
            ranking_name = interaction.guild.name
            Database.create_new_ranking(
                ranking_name.replace(" ", "_"), interaction.guild.id)

            data = Database.fetch_rankingIds(interaction.guild.id)
            rankingID = data[0][0]
            await interaction.response.send_message(f"Created your first ranking with name of server: {interaction.guild.name}.  Miau! (●'◡'●)")

        # too many ranking names, cannot pick cause no ranking_name in message
        else:
            await interaction.response.send_message("In your server are several rankings, choose one and call me again! Miau! (●'◡'●)")
            return

    # ranking_name in message
    else:
        data = Database.fetch_rankingIds(interaction.guild.id, ranking_name)
        if (len(data) != 1):
            await interaction.response.send_message("Invalid ranking name. If you can, correct it, pleasee~~~? ◕‿↼")
            return
        else:
            rankingID = data[0][0]

    data = Database.fetch_user_from_points(user, rankingID)
    if (len(data) == 0):
        Database.insert_user_to_points(user, rankingID)
        Database.increase_total_memebers_in_ranking(rankingID)
        await interaction.response.send_message(f"Added {user} to the {ranking_name} ranking! You're welcome! Miau ＼(´ ε｀ )／")
    else:
        await interaction.response.send_message(f"User {user} is already in the DB ( ͡°Ɛ ͡°)")


@bot.slash_command(guild_ids=[1030024780314845234])
async def remove_from_ranking(interaction: Interaction, user:Optional[str], ranking_name: Optional[str]):
    """Removing member from ranking.

    Parameters
    ----------
    interaction: Interaction
        The interaction object
    user: Optional[str]
        Mention user or let it blank to remove yourself
    ranking_name: Optional[str]
        Type ranking name to which you want to remove someone or leave blank if only 1 ranking exist
    """
    rankingID = -1
    if user is None:
        user = interaction.user.mention
    # check if custom name or authorName is a mention
    if (not (user.startswith("<@") and user.endswith(">"))):
        await interaction.response.send_message("Invalid user, pleeesa use user mentions only!  Miau! (●'◡'●)")
        return

    # no RankingName in message
    if ranking_name is None:
        data = Database.fetch_rankings_in_guild(interaction.guild.id)

        # found one default ranking
        if (len(data) == 1):
            ranking_name = data[0][0]
            rankingID = data[0][1]

        # no ranking for guild
        elif (len(data) == 0):
            # create new ranking
            ranking_name = interaction.guild.name
            Database.create_new_ranking(
                ranking_name.replace(" ", "_"), interaction.guild.id)

            data = Database.fetch_rankingIds(interaction.guild.id)
            rankingID = data[0][0]
            await interaction.response.send_message(f"Created your first ranking with name of server: {interaction.guild.name}.  Miau! (●'◡'●)")

        # too many ranking names, cannot pick cause no ranking_name in message
        else:
            await interaction.response.send_message("In your server are several rankings, choose one and call me again! Miau! (●'◡'●)")
            return

    # RankingName in message
    else:
        data = Database.fetch_rankingIds(ctx.guild.id, ranking_name)
        if (len(data) != 1):
            await ctx.send("Invalid ranking name. If you can, correct it, pleasee~~~? ◕‿↼")
            return
        else:
            rankingID = data[0][0]

    user = Database.fetch_user_from_points(user, rankingID)
    if (len(user) == 0):
        await ctx.send(f"User {user} is not in the {ranking_name} ranking ( ͡°Ɛ ͡°)")
        return
    else:
        Database.decrease_total_memebers_in_ranking(rankingID)
        Database.remove_user_from_points(user, rankingID)
        await ctx.send(f"Removed {user} from the {ranking_name} ranking :( We will miss You! Miau ＼(´ ε｀ )／")
        return


@bot.slash_command(guild_ids=[1030024780314845234])
async def create_new_ranking(interaction: Interaction, ranking_name: str):
    """Create a new ranking for your server!

    Parameters
    ----------
    interaction: Interaction
        The interaction object
    ranking_name: str
        Type ranking name!
    """
    if Database.create_new_ranking(ranking_name.replace(" ", "_"), interaction.guild.id):
        await interaction.response.send_message("You've added a new ranking! Congratulation! Miau! (●'◡'●)")
    else:
        await interaction.response.send_message("Oh! There was a problem. Maybe you made a typo in name?  Miau! (︶︹︺)")


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

@bot.slash_command(guild_ids=[1030024780314845234])
async def vote(interaction: Interaction, person: str, description: str, points: Optional[int], ranking_name: Optional[str]):
    """Vot for adding/removing points for person. Add description to voting for context. Points and ranking name are optional parameters. Default is +1 point.

    Parameters
    ----------
    interaction: Interaction
        The interaction object
    person: str
        Mention user by "@PersonName" to whom you want vote
    description: str
        Short description of voting context
    points: Optional[int]
        How many points you want to add. Write negative num to remove x points
    ranking_name: Optional[str]
        Type ranking name from ranking or leave blank if there is only 1 ranking in your server
    """
    rankingId = 0
    if ranking_name is None:
        data = Database.fetch_rankings_in_guild(interaction.guild.id)
        if (len(data) == 1):
            rankingId = data[0][1]
            ranking_name = data[0][0]
        else:
            await interaction.response.send_message("In your server are several rankings, choose one and call me again! Miau! (●'◡'●)")
            return
    else:
        ranking = Database.fetch_rankingIds(interaction.guild.id, ranking_name)
        if (len(ranking) != 1):
            await interaction.response.send_message("Invalid ranking name. If you can, correct it, pleasee~~~? ◕‿↼")
            return

        rankingId = ranking[0][0]

    nickname = ""
    for x in interaction.guild.members:
        if (x.mention == person):
            nickname = x.name
            break

    if (nickname == ""):
        await interaction.response.send_message("Invalid user, pleeesa use user mentions only!  Miau! (●'◡'●)")
        return
    users = Database.fetch_users_from_ranking(rankingId)
    user = Helper.find_user_by_string_name(nickname, bot)
    if not any(user.mention in x for x in users):
        await interaction.response.send_message("User is not in the ranking. Miau! (●'◡'●)")
        return

    if points is None:
        points = 1
    elif (points == 0):
        await interaction.response.send_message(f"Voting for 0 points, are u silly? Meow (◕‿◕✿)")
        return

    print("Started voting")
    embed = discord.Embed(
        title=f"Voting Battle in {ranking_name}", color=0xffff00)
    if (points > 0):
        embed.add_field(
            name=f"{interaction.user.name} wants to add {points} point(s) to {nickname} because:", value=f"{description}", inline=False)
    if (points < 0):
        embed.add_field(
            name=f"{interaction.user.name} wants to remove {points} point(s) from {nickname} because:", value=f"{description}", inline=False)
    embed.add_field(name="Approve voting by reacting 👍, votes left:",
                    value=NUMBER_OF_VOTES_NEEDED, inline=True)
    embed.add_field(
        name="To reject react 👎, votes left:", value=NUMBER_OF_VOTES_NEEDED, inline=True)
    embed.set_footer(text="#Rankuś ＼(´ ε｀ )／")
    await interaction.response.send_message(embed=embed)

    message: nextcord.Message
    async for message in interaction.channel.history():
        if not message.embeds:
            continue
        if message.embeds[0].title == embed.title:
            vote = message
            break
    else:
        # something broke
        return

    await vote.add_reaction("👍")
    await vote.add_reaction("👎")

@bot.command()
async def showRanking(ctx, *args):
    #arg: optional rankingName
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
        mention = row[0]
        user = Helper.find_user_by_mention(mention, bot)
        if (user != None):
            _row = [user.name, row[1]]
            tb.add_row(_row)
    tb.sortby = "Points"
    tb.reversesort = True
    await ctx.send(f"```\n{tb}```")

@bot.slash_command(guild_ids=[1030024780314845234])
async def show_ranking(interaction: Interaction, ranking_name: Optional[str]):
    """Show actual points table for ranking

    Parameters
    ----------
    interaction: Interaction
        The interaction object
    ranking_name: Optional[str]
        Type ranking name or leave blank if there is only 1 ranking in your server!
    """
    if ranking_name is None:
        rankings = Database.fetch_rankings_in_guild(interaction.guild.id)
        # found one default ranking
        if (len(rankings) == 1):
            ranking_name = rankings[0][0]
        else:
            await interaction.response.send_message("No results. Miau! (●'◡'●) \nRemember: ranking name has no whitespaces! \nType ranking name if you didn't")
            return

    # fetch data from ranking
    data = Database.fetch_user_with_points(ranking_name, interaction.guild.id)
    tb = pt()
    tb.title = ranking_name
    tb.field_names = ["User Name", "Points"]
    for row in data:
        mention = row[0]
        user = Helper.find_user_by_mention(mention, bot)
        if (user != None):
            _row = [user.name, row[1]]
            tb.add_row(_row)
    tb.sortby = "Points"
    tb.reversesort = True
    await interaction.response.send_message(f"```\n{tb}```")

bot.run(TOKEN)
