
from cogs.ext.utils import *


async def setup(bot: commands.Bot):
    # guilds=[discord.Object(id=....)]
    await bot.add_cog(WarningsCommands(bot, configManager))




class WarningsCommands(commands.Cog, name="WarningsCommands"):

    def __init__(self, bot: commands.Bot, configManager: ConfigManager):
        self.bot = bot
        self.configManager = configManager

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="warn")
    @app_commands.describe(member=configManager.getMentionMemberArg(), reason=configManager.getReasonArg())
    async def warn(self, interaction: discord.Interaction, member: str, reason: str):
        try:
            member = getMember(interaction, get_member_id_from_mention(member))
            role = getRole(interaction, configManager.getWarningRoleID())
            await member.add_roles(role)
            placeholders = {self.configManager.getRoleNamePlaceholder(): role.name,
                            self.configManager.getUsernamePlaceholder(): member.name,
                            self.configManager.getReasonPlaceholder(): reason}

            addWarningToConfig(str(member.id), reason)

            await sendResponse(interaction, self.configManager.getWarnMemberKey(), placeholders)

        except Exception as e:
            placeholders = {self.configManager.getErrorPlaceholder(): e}
            await sendResponse(interaction, self.configManager.getUnknownErrorKey(), placeholders)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="warnings")
    @app_commands.describe(member=configManager.getMentionMemberArg())
    async def warnings(self, interaction: discord.Interaction, member: str):
        try:
            member = getMember(interaction, get_member_id_from_mention(member))
            r_id = getRole(interaction, configManager.getWarningRoleID()).id
            for role in member.roles:
                if role.id == r_id:
                    placeholders = {self.configManager.getRoleNamePlaceholder(): role.name,
                                    self.configManager.getUsernamePlaceholder(): member.name,
                                    self.configManager.getReasonPlaceholder(): configManager.warning_data[
                                        str(member.id)]}
                    await sendResponse(interaction, self.configManager.getViewWarnMembersKey(), placeholders)
                    return

        except Exception as e:
            placeholders = {self.configManager.getErrorPlaceholder(): e}
            await sendResponse(interaction, self.configManager.getUnknownErrorKey(), placeholders)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="clearwarnings")
    @app_commands.describe(member=configManager.getMentionMemberArg(), reason=configManager.getReasonArg())
    async def clearwarnings(self, interaction: discord.Interaction, member: str, reason: str = ""):
        try:
            member = getMember(interaction, get_member_id_from_mention(member))
            role = getRole(interaction, configManager.getWarningRoleID())
            await member.remove_roles(role, reason=reason)
            placeholders = {self.configManager.getRoleNamePlaceholder(): role.name,
                            self.configManager.getUsernamePlaceholder(): member.name,
                            self.configManager.getReasonPlaceholder(): reason}

            removeWarningFromConfig(str(member.id))

            await sendResponse(interaction, self.configManager.getClearWarningsMemberKey(), placeholders)

        except Exception as e:
            placeholders = {self.configManager.getErrorPlaceholder(): e}
            await sendResponse(interaction, self.configManager.getUnknownErrorKey(), placeholders)


