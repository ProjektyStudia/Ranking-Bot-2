class Helper:
    @classmethod
    def find_user_by_string_name(self, name: str, bot):
        for user in bot.get_all_members():
            if user.name == name:
                return user
        return None
