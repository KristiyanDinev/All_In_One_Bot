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
        if await handleRestricted(interaction, "warn"):
            return

        member = getMember(interaction, get_member_id_from_mention(member))
        if member is None:
            await handleInvalidMember(interaction, "warn")
            return

        roles = getWarningRolesFromLevel(interaction, getUserWarningLevel(member) + 1)

        try:
            for r in roles:
                await member.add_roles(r, reason=reason)

                await handleMessage(interaction, "warn",
                                    placeholders={configManager.getUsernamePlaceholder(): member.name,
                                                  configManager.getReasonPlaceholder(): reason})

        except Exception as e:
            print(e)
            await handleErrors(interaction, "warn", e)

    @app_commands.command(description=configManager.getCommandArgDescription("warnings", "description"))
    @app_commands.describe(
        member=configManager.getCommandArgDescription("warnings", configManager.getMentionMemberKey()))
    async def warnings(self, interaction: discord.Interaction, member: str):
        if await handleRestricted(interaction, "warnings"):
            return

        member = getMember(interaction, get_member_id_from_mention(member))
        if member is None:
            await handleInvalidMember(interaction, "warnings")
            return

        roles = getRoleIdFromRoles(getWarningRolesFromLevel(interaction, getUserWarningLevel(member)))
        for role in member.roles:
            if role.id in roles:
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
        if await handleRestricted(interaction, "clearwarnings"):
            return

        member = getMember(interaction, get_member_id_from_mention(member))
        if member is None:
            await handleInvalidMember(interaction, "warnings")
            return

        allRoles = []
        for level in range(1, configManager.getWarningLevels()+1):
            roleData = configManager.getWarningDataForLevel(level)
            if len(roleData) == 0:
                continue

            roles_id = roleData.get("roles_id", None)
            if roles_id is not None:
                for r_id in roles_id:
                    r = interaction.guild.get_role(r_id)
                    if r is not None:
                        allRoles.append(r)

        try:
            for role in allRoles:
                await member.remove_roles(role, reason=reason)

                await handleMessage(interaction, "clearwarnings",
                                    placeholders={configManager.getUsernamePlaceholder(): member.name,
                                configManager.getReasonPlaceholder(): reason})

        except Exception as e:
            await handleErrors(interaction, "clearwarnings", e)
