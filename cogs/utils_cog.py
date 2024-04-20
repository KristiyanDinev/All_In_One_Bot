import discord.errors
from cogs.ext.utils import *


async def setup(bot: commands.Bot):
    # guilds=[discord.Object(id=....)]
    await bot.add_cog(UtilsCog(bot, configManager))


class UtilsCog(commands.Cog, name="Utils"):

    def __init__(self, bot: commands.Bot, configManager: ConfigManager):
        self.bot = bot
        self.configManager = configManager

    @app_commands.command(description=configManager.getCommandData("avatar")[configManager.wordDescription()])
    @app_commands.describe(member=configManager.getCommandArgs("avatar", configManager.getMentionMemberKey()))
    async def avatar(self, interaction: discord.Interaction, member: str = ""):
        b = member
        if member == "":
            member: discord.Member = interaction.user
        else:
            member: discord.Member = getMember(interaction, get_member_id_from_mention(member))

        if member is None:
            placeholders = {self.configManager.getUsernamePlaceholder(): b}
            await sendResponse(interaction, "avatar", self.configManager.getInvalidMemberKey(), placeholders)
            return

        placeholders = {self.configManager.getUsernamePlaceholder(): member.name,
                        self.configManager.getAvatarUrlPlaceholder(): member.avatar.url}
        await sendResponse(interaction, "avatar", configManager.getAvatarMessageKey(), placeholders)

    @app_commands.command(description=configManager.getCommandData("invite")[configManager.wordDescription()])
    async def invite(self, interaction: discord.Interaction):
        try:
            # https://discord.com/oauth2/authorize?client_id=1223731465309917204&scope=applications.commands%20bot&permissions=8
            placeholders = {configManager.getInvitePlaceholder(): "https://discord.com/oauth2/authorize?client_id=" +
                                                                  str(self.bot.user.id) + "&scope=applications.commands%20bot&permissions=8"}
            await sendResponse(interaction, "invite", self.configManager.getClearWarningsMemberKey(), placeholders)

        except Exception as e:
            placeholders = {self.configManager.getErrorPlaceholder(): e}
            await sendResponse(interaction, "invite", self.configManager.getUnknownErrorKey(), placeholders)

    @app_commands.command(description=configManager.getCommandData("ping")[configManager.wordDescription()])
    async def ping(self, interaction: discord.Interaction):
        try:
            placeholders = {self.configManager.getBotLatencyPlaceholder(): str(round(self.bot.latency, 1))}
            await sendResponse(interaction, "ping", self.configManager.getPingKey(), placeholders)

        except Exception as e:
            placeholders = {self.configManager.getErrorPlaceholder(): e}
            await sendResponse(interaction, "ping", self.configManager.getUnknownErrorKey(), placeholders)
