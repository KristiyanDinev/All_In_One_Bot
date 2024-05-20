from __future__ import annotations

from discord import app_commands
from discord.ext import commands

from cogs.ext.utils.utils import *
import cogs.ext.utils.messages as messages


async def setup(bot: commands.Bot):
    # guilds=[discord.Object(id=....)]
    await bot.add_cog(WarningsCommands(bot))


class WarningsCommands(commands.Cog, name="Warnings"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(description=configManager.getCommandArgDescription("warn", "description"))
    @app_commands.describe(member=configManager.getCommandArgDescription("warn", configManager.getMentionMemberKey()),
                           reason=configManager.getCommandArgDescription("warn", configManager.getReasonKey()))
    async def warn(self, interaction: discord.Interaction, member: str, reason: str):
        if await messages.handleRestricted(self.bot, interaction, "warn"):
            return

        member = getMember(interaction, getMemberIdFromMention(member))
        if member is None:
            await messages.handleInvalidMember(self.bot, interaction, "warn")
            return

        nextLevel = getUserWarningLevel(member) + 1
        roles = getWarningRolesFromLevel(interaction, nextLevel)
        warningData = configManager.getWarningDataForLevel(nextLevel)

        try:
            for r in roles:
                await giveRoleToUser(member, r, reason=reason)
                await member.add_roles(r, reason=reason)

                await messages.handleMessage(self.bot, interaction, "warn",
                                             placeholders={configManager.getUsernamePlaceholder(): member.name,
                                                           configManager.getReasonPlaceholder(): reason})

            sendMessages: list | None = warningData.get("send_messages", None)
            if sendMessages is not None:
                for msg in sendMessages:
                    await messages.handleMessage(self.bot, interaction, msg,
                                                 placeholders={configManager.getUsernamePlaceholder(): member.name,
                                                               configManager.getReasonPlaceholder(): reason})

        except Exception as e:
            await messages.handleErrors(self.bot, interaction, "warn", e)

    @app_commands.command(description=configManager.getCommandArgDescription("warnings", "description"))
    @app_commands.describe(
        member=configManager.getCommandArgDescription("warnings", configManager.getMentionMemberKey()))
    async def warnings(self, interaction: discord.Interaction, member: str):
        if await messages.handleRestricted(self.bot, interaction, "warnings"):
            return

        member = getMember(interaction, getMemberIdFromMention(member))
        if member is None:
            await messages.handleInvalidMember(self.bot, interaction, "warnings")
            return

        roles = getRoleIdFromRoles(getWarningRolesFromLevel(interaction, getUserWarningLevel(member)))
        for role in member.roles:
            if role.id in roles:
                try:
                    await messages.handleMessage(self.bot, interaction, "warnings",
                                                 placeholders={configManager.getRoleNamePlaceholder(): role.name,
                                                               configManager.getUsernamePlaceholder(): member.name,
                                                               configManager.getReasonPlaceholder():
                                                                   configManager.warning_data[
                                                                       str(member.id)]})
                    return

                except Exception as e:
                    await messages.handleErrors(self.bot, interaction, "warnings", e)

    @app_commands.command(description=configManager.getCommandArgDescription("clearwarnings", "description"))
    @app_commands.describe(
        member=configManager.getCommandArgDescription("clearwarnings", configManager.getMentionMemberKey()),
        reason=configManager.getCommandArgDescription("clearwarnings", configManager.getReasonKey()))
    async def clearwarnings(self, interaction: discord.Interaction, member: str, reason: str = ""):
        if await messages.handleRestricted(self.bot, interaction, "clearwarnings"):
            return

        member = getMember(interaction, getMemberIdFromMention(member))
        if member is None:
            await messages.handleInvalidMember(self.bot, interaction, "warnings")
            return

        allRoles = []
        for level in range(1, configManager.getWarningLevels() + 1):
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
                await removeRoleToUser(member, role, reason=reason)

                await messages.handleMessage(self.bot, interaction, "clearwarnings",
                                             placeholders={configManager.getUsernamePlaceholder(): member.name,
                                                           configManager.getReasonPlaceholder(): reason})

        except Exception as e:
            await messages.handleErrors(interaction, "clearwarnings", e)

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        return
