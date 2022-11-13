import nextcord
from nextcord.ext import commands
from nextcord import Client
import sqlite3


class Database:
    # sqlite
    connection = sqlite3.connect("Database/cham.db")
    cursor = connection.cursor()

    @classmethod
    async def fetch_messages_from_db(self):
        results = []
        print("Started fetching data from db")
        self.cursor.execute(
            f"""SELECT Message_id, Agreed, Rejected, NeedTotalVotes FROM Messages""")
        data = self.cursor.fetchall()

        for record in data:
            results.append(record)

        print("Finished fetching")
        return results

    @classmethod
    async def insert_message_to_db(self, message_id, needVotes):
        self.cursor.execute(
            f"""INSERT INTO Messages (Message_id, Agreed, Rejected, NeedTotalVotes) VALUES('{message_id}', 0, 0, {needVotes});""")
        self.connection.commit()
        results = await self.fetch_messages_from_db()
        return results

    @classmethod
    async def update_message_votes(self, message_id, vote_type, action, vote_count):
        if action == "Add":
            self.cursor.execute(
                f"""UPDATE Messages SET {vote_type} = {vote_count} where Message_id = '{message_id}';""")
        elif action == "Remove":
            self.cursor.execute(
                f"""UPDATE Messages SET {vote_type} = {vote_count} where Message_id = '{message_id}';""")
        else:
            return
        self.connection.commit()
        return vote_count

    @classmethod
    async def delete_message_from_db(self, message_id):
        self.cursor.execute(
            f"""DELETE FROM Messages where Message_id = '{message_id}';""")
        self.connection.commit()
        results = await self.fetch_messages_from_db()
        return results

    @classmethod
    async def change_user_points(self, user_id, points):
        self.cursor.execute(
            f"""UPDATE Points SET Points = Points + {points} where User = '{user_id}';""")
        self.connection.commit()
        results = await self.fetch_messages_from_db()
        return results

    @classmethod
    def fetch_rankings_in_guild(self, guildId):
        self.cursor.execute(
            f"""SELECT RankingName, RankingID from Rankings WHERE GuildID='{guildId}'""")
        response = self.cursor.fetchall()

        return response

    @classmethod
    def create_new_ranking(self, name, guildId):
        self.cursor.execute(
            f"""INSERT INTO Rankings (RankingName, GuildID) VALUES ('{name}','{guildId}')""")
        self.connection.commit()

    @classmethod
    def fetch_rankingIds(self, guildId):
        self.cursor.execute(
            f"""SELECT RankingID from Rankings WHERE GuildID='{guildId}'""")
        return self.cursor.fetchall()

    @classmethod
    def fetch_rankingIds(self, guildId, rankingName):
        self.cursor.execute(
            f"""SELECT RankingID from Rankings WHERE GuildID='{guildId}' AND RankingName='{rankingName}'""")
        return self.cursor.fetchall()

    @classmethod
    def fetch_user_from_points(self, userToDb, rankingId):
        self.cursor.execute(
            f"""SELECT User from Points WHERE User='{userToDb}' AND RankingID='{rankingId}'""")
        return self.cursor.fetchall()

    @classmethod
    def insert_user_to_points(self, userToDb, rankingId):
        self.cursor.execute(
            f"""INSERT INTO Points VALUES('{userToDb}', {rankingId} , {int("0")})""")
        self.connection.commit()

    @classmethod
    def remove_user_from_points(self, userToDb, rankingId):
        self.cursor.execute(
            f"""DELETE FROM Points WHERE User='{userToDb}' AND RankingID='{rankingId}'""")
        self.connection.commit()

    @classmethod
    def increase_total_memebers_in_ranking(self, rankingId):
        self.cursor.execute(
            f"""UPDATE Rankings SET NumberOfMembers = NumberOfMembers + 1 where RankingID = {rankingId};""")
        self.connection.commit()

    @classmethod
    def decrease_total_memebers_in_ranking(self, rankingId):
        self.cursor.execute(
            f"""UPDATE Rankings SET NumberOfMembers = NumberOfMembers - 1 where RankingID = {rankingId};""")
        self.connection.commit()

    @classmethod
    def fetch_ranking_name(self, rankingName, guildId):
        self.cursor.execute(
            f"""SELECT RankingName from Rankings WHERE RankingName='{rankingName}' and GuildID='{guildId}'""")
        response = self.cursor.fetchall()

        return response[0][0]

    @classmethod
    def fetch_user_with_points(self, rankingName, guildId):
        self.cursor.execute(
            f"""SELECT p.User, p.Points from Points p INNER JOIN Rankings r ON r.RankingID = p.RankingID WHERE r.RankingName='{rankingName}' AND r.GuildID={guildId}""")
        response = self.cursor.fetchall()

        return response

    @classmethod
    def fetch_users_from_ranking(self, rankingId):
        self.cursor.execute(
            f"""SELECT User from Points WHERE RankingID={rankingId}""")
        response = self.cursor.fetchall()

        return response

    def __del__(self):
        self.connection.close()
