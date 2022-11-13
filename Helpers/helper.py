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
