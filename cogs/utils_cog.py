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
        if await handleRestricted(interaction, "avatar"):
            return

        if member == "":
            member: discord.Member = interaction.user
        else:
            member: discord.Member = getMember(interaction, get_member_id_from_mention(member))

        if member is None:
            await handleInvalidMember(interaction, "avatar")
            return

        placeholders = {configManager.getUsernamePlaceholder(): member.name,
                        configManager.getAvatarUrlPlaceholder(): member.avatar.url}
        await handleMessage(interaction, "avatar", placeholders=placeholders)

    @app_commands.command(description=configManager.getCommandArgDescription("invite", "description"))
    @app_commands.describe(bot_id=configManager.getCommandArgDescription("invite", configManager.getMemberIDKey()),
                           permissions=configManager.getCommandArgDescription("invite", configManager.getNumberKey()))
    async def invite(self, interaction: discord.Interaction, bot_id: str, permissions: str):
        if await handleRestricted(interaction, "invite"):
            return

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
        if await handleRestricted(interaction, "ping"):
            return

        await handleMessage(interaction, "ping",
                            placeholders={configManager.getBotLatencyPlaceholder(): str(round(self.bot.latency, 1))})


    @app_commands.command(description=configManager.getCommandArgDescription("dm", "description"))
    @app_commands.describe(member=configManager.getCommandArgDescription("dm", configManager.getMentionMemberKey()),
                           message=configManager.getCommandArgDescription("dm", configManager.getEnterMessageKey()))
    async def dm(self, interaction: discord.Interaction, message: str, member: str = ""):
        if await handleRestricted(interaction, "dm"):
            return

        if len(message.replace(" ", "")) == 0:
            await handleInvalidArg(interaction, "dm")
            return

        if member == "":
            member: discord.Member = interaction.user
        else:
            member: discord.Member = getMember(interaction, get_member_id_from_mention(member))

        if member is None:
            await handleInvalidMember(interaction, "dm")
            return


        await handleMessage(interaction, "dm", placeholders={configManager.getUsernamePlaceholder(): interaction.user.name,
                        configManager.getMessagePlaceholder(): message}, dm_user=member)
