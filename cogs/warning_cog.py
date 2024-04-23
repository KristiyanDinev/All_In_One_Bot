from cogs.ext.utils import *


async def setup(bot: commands.Bot):
    # guilds=[discord.Object(id=....)]
    await bot.add_cog(WarningsCommands(bot))


class WarningsCommands(commands.Cog, name="WarningsCommands"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(description=configManager.getCommandArgDescription("warn", "description"))
    @app_commands.describe(member=configManager.getCommandArgDescription("warn", configManager.getMentionMemberKey()),
                           reason=configManager.getCommandArgDescription("warn", configManager.getReasonKey()))
    async def warn(self, interaction: discord.Interaction, member: str, reason: str):
        member = getMember(interaction, get_member_id_from_mention(member))
        if member is None:
            await handleInvalidMember(interaction, "warn")
            return

        role = getRole(interaction, configManager.getWarningRoleID())
        if role is None:
            await handleInvalidRole(interaction, "warn")
            return

        try:
            await member.add_roles(role)

            addWarningToConfig(str(member.id), reason)

            await handleMessage(interaction, "warn",
                                placeholders={configManager.getRoleNamePlaceholder(): role.name,
                                              configManager.getUsernamePlaceholder(): member.name,
                                              configManager.getReasonPlaceholder(): reason})

        except Exception as e:
            await handleErrors(interaction, "warn", e)

    @app_commands.command(description=configManager.getCommandArgDescription("warnings", "description"))
    @app_commands.describe(
        member=configManager.getCommandArgDescription("warnings", configManager.getMentionMemberKey()))
    async def warnings(self, interaction: discord.Interaction, member: str):
        member = getMember(interaction, get_member_id_from_mention(member))
        if member is None:
            await handleInvalidMember(interaction, "warnings")
            return

        role = getRole(interaction, configManager.getWarningRoleID())
        if role is None:
            await handleInvalidRole(interaction, "warnings")
            return

        role_id = role.id
        for role in member.roles:
            if role.id == role_id:
                try:
                    await handleMessage(interaction, "warnings",
                                        placeholders={configManager.getRoleNamePlaceholder(): role.name,
                                                      configManager.getUsernamePlaceholder(): member.name,
                                                      configManager.getReasonPlaceholder(): configManager.warning_data[
                                                          str(member.id)]})
                    return

                except Exception as e:
                    await handleErrors(interaction, "warnings", e)


    @app_commands.command(description=configManager.getCommandArgDescription("clearwarnings", "description"))
    @app_commands.describe(member=configManager.getCommandArgDescription("clearwarnings", configManager.getMentionMemberKey()),
                           reason=configManager.getCommandArgDescription("clearwarnings", configManager.getReasonKey()))
    async def clearwarnings(self, interaction: discord.Interaction, member: str, reason: str = ""):
        member = getMember(interaction, get_member_id_from_mention(member))
        if member is None:
            await handleInvalidMember(interaction, "warnings")
            return

        role = getRole(interaction, configManager.getWarningRoleID())
        if role is None:
            await handleInvalidRole(interaction, "warnings")
            return

        try:

            await member.remove_roles(role, reason=reason)

            removeWarningFromConfig(str(member.id))

            await handleMessage(interaction, "clearwarnings",
                                placeholders={configManager.getRoleNamePlaceholder(): role.name,
                            configManager.getUsernamePlaceholder(): member.name,
                            configManager.getReasonPlaceholder(): reason})

        except Exception as e:
            await handleErrors(interaction, "clearwarnings", e)
