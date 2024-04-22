import discord.errors
from cogs.ext.utils import *


async def setup(bot: commands.Bot):
    # guilds=[discord.Object(id=....)]
    await bot.add_cog(UtilsCog(bot))


class UtilsCog(commands.Cog, name="Utils"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(description=configManager.getCommandArgDescription("avatar", "description"))
    @app_commands.describe(member=configManager.getCommandArgDescription("avatar", configManager.getMentionMemberKey()))
    async def avatar(self, interaction: discord.Interaction, member: str = ""):
        if member == "":
            member: discord.Member = interaction.user
        else:
            member: discord.Member = getMember(interaction, get_member_id_from_mention(member))

        if member is None:
            placeholders = {configManager.getUsernamePlaceholder(): "invalid username"}
            await handleMessage(interaction, "avatar", error_name=configManager.getInvalidMemberKey(),
                                placeholders=placeholders)
            return

        placeholders = {configManager.getUsernamePlaceholder(): member.name,
                        configManager.getAvatarUrlPlaceholder(): member.avatar.url}
        await handleMessage(interaction, "avatar", placeholders=placeholders)

    @app_commands.command(description=configManager.getCommandArgDescription("invite", "description"))
    @app_commands.describe(bot_id=configManager.getCommandArgDescription("invite", configManager.getMemberIDKey()),
                           permissions=configManager.getCommandArgDescription("invite", configManager.getNumberKey()))
    async def invite(self, interaction: discord.Interaction, bot_id: str, permissions: str):
        if not bot_id.isdigit() or not permissions.isdigit():
            await handleMessage(interaction, "invite", error_name=configManager.getInvalidArgsKey(),
                                placeholders={
                                    configManager.getErrorPlaceholder():
                                        configManager.getCommandMessages("invite", configManager.getNumberKey())})
            return
        # https://discord.com/oauth2/authorize?client_id=1223731465309917204&scope=applications.commands%20bot&permissions=8
        await handleMessage(interaction, "invite", placeholders={
            configManager.getInvitePlaceholder(): "https://discord.com/oauth2/authorize?client_id=" +
                                                  bot_id + "&scope=applications.commands%20bot&permissions=" +
                                                  permissions})

    @app_commands.command(description=configManager.getCommandArgDescription("ping", "description"))
    async def ping(self, interaction: discord.Interaction):
        await handleMessage(interaction, "ping", configManager.getPingKey(),
                            placeholders={configManager.getBotLatencyPlaceholder(): str(round(self.bot.latency, 1))})
