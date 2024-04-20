
from cogs.ext.utils import *


async def setup(bot: commands.Bot):
    # guilds=[discord.Object(id=....)]
    await bot.add_cog(LevelingCog(bot, configManager))




class LevelingCog(commands.Cog, name="Leveling"):

    def __init__(self, bot: commands.Bot, configManager: ConfigManager):
        self.bot = bot
        self.configManager = configManager


