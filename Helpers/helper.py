import math
from Database.db import Database


class Helper:
    @classmethod
    def find_user_by_string_name(self, name: str, bot):
        for user in bot.get_all_members():
            if user.name == name:
                return user
        return None

    def find_user_by_mention(mention: str, bot):
        for user in bot.get_all_members():
            if user.mention == mention:
                return user
        return None

    @classmethod
    def get_number_of_votes(self, rankingName, guildId):
        total_members = Database.fetch_total_members(rankingName, guildId)
        number_of_votes_needed = int(math.sqrt(total_members))
        return number_of_votes_needed
