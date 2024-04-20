import datetime

import discord.errors
from cogs.ext.utils import *


async def setup(bot: commands.Bot):
    # guilds=[discord.Object(id=....)]
    await bot.add_cog(ModeratorCog(bot, configManager))



class ModeratorCog(commands.Cog, name="Moderator"):

    def __init__(self, bot: commands.Bot, configManager: ConfigManager):
        self.bot = bot
        self.configManager = configManager

    @app_commands.command(description=configManager.getCommandData("addrole")[configManager.wordDescription()])
    @app_commands.describe(member=configManager.getCommandArgs("addrole", configManager.getMentionMemberKey()),
                           role=configManager.getCommandArgs("addrole", configManager.getMentionRoleKey()),
                           reason=configManager.getCommandArgs("addrole", configManager.getReasonKey()))
    async def addrole(self, interaction: discord.Interaction, member: str, role: str, reason: str = ""):
        member_obj: discord.Member = getMember(interaction, get_member_id_from_mention(member))
        if member_obj is None:
            placeholders = {self.configManager.getUsernamePlaceholder(): member}
            await sendResponse(interaction, "addrole", self.configManager.getInvalidMemberKey(), placeholders)
            return

        role_obj = getRole(interaction, get_role_id_from_mention(role))
        if role_obj is None:
            placeholders = {self.configManager.getRoleNamePlaceholder(): role}
            await sendResponse(interaction, "addrole", self.configManager.getInvalidRoleKey(), placeholders)
            return

        try:
            await member_obj.add_roles(role_obj, reason=reason)
            placeholders = {self.configManager.getRoleNamePlaceholder(): role_obj.name,
                            self.configManager.getReasonPlaceholder(): reason}
            await sendResponse(interaction, "addrole", self.configManager.getAddedRoleKey(), placeholders)

        except Exception as e:
            placeholders = {self.configManager.getErrorPlaceholder(): e}
            await sendResponse(interaction, "addrole", self.configManager.getUnknownErrorKey(), placeholders)

    @app_commands.command(description=configManager.getCommandData("removerole")[configManager.wordDescription()])
    @app_commands.describe(member=configManager.getCommandArgs("removerole", configManager.getMentionMemberKey()),
                           role=configManager.getCommandArgs("removerole", configManager.getMentionRoleKey()),
                           reason=configManager.getCommandArgs("removerole", configManager.getReasonKey()))
    async def removerole(self, interaction: discord.Interaction, member: str, role: str, reason: str = ""):
        member_obj: discord.Member = getMember(interaction, get_member_id_from_mention(member))
        if member_obj is None:
            placeholders = {self.configManager.getUsernamePlaceholder(): member}
            await sendResponse(interaction, "removerole", self.configManager.getInvalidMemberKey(), placeholders)
            return

        role_obj = getRole(interaction, get_role_id_from_mention(role))
        if role_obj is None:
            placeholders = {self.configManager.getRoleNamePlaceholder(): role}
            await sendResponse(interaction, "removerole", self.configManager.getInvalidRoleKey(), placeholders)
            return

        try:
            await member_obj.remove_roles(role_obj, reason=reason)
            placeholders = {self.configManager.getRoleNamePlaceholder(): role_obj.name,
                            self.configManager.getReasonPlaceholder(): reason}
            await sendResponse(interaction, "removerole", self.configManager.getAddedRoleKey(), placeholders)

        except Exception as e:
            placeholders = {self.configManager.getErrorPlaceholder(): e}
            await sendResponse(interaction, "removerole", self.configManager.getUnknownErrorKey(), placeholders)




    @app_commands.command(description=configManager.getCommandData("ban")[configManager.wordDescription()])
    @app_commands.describe(member=configManager.getCommandArgs("ban", configManager.getMentionMemberKey()),
                           reason=configManager.getCommandArgs("ban", configManager.getReasonKey()))
    async def ban(self, interaction: discord.Interaction, member: str, reason: str):
        try:
            member = getMember(interaction, get_member_id_from_mention(member))
            await member.ban(reason=reason)
            placeholders = {self.configManager.getUsernamePlaceholder(): member.name,
                            self.configManager.getReasonPlaceholder(): reason}
            await sendResponse(interaction, "ban", self.configManager.getBanMemberKey(), placeholders)
        except Exception as e:
            placeholders = {self.configManager.getErrorPlaceholder(): e}
            await sendResponse(interaction, "ban", self.configManager.getUnknownErrorKey(), placeholders)


    @app_commands.command(description=configManager.getCommandData("unban")[configManager.wordDescription()])
    @app_commands.describe(member=configManager.getCommandArgs("unban", configManager.getMentionMemberKey()),
                           reason=configManager.getCommandArgs("unban", configManager.getReasonKey()))
    async def unban(self, interaction: discord.Interaction, member: str, reason: str):
        try:
            member_id = int(member)
            async for ban_entry in interaction.guild.bans():
                user = ban_entry.user
                if user.id == member_id:
                    await interaction.guild.unban(user, reason=reason)
                    placeholders = {self.configManager.getUsernamePlaceholder(): user.name}
                    await sendResponse(interaction, self.configManager.getUnbanMemberKey(), placeholders)
                    return

        except Exception as e:
            placeholders = {self.configManager.getErrorPlaceholder(): e}
            await sendResponse(interaction, self.configManager.getUnknownErrorKey(), placeholders)


    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="blacklist")
    @app_commands.describe(words=configManager.getBlacklistWordsArg())
    async def blacklist(self, interaction: discord.Interaction, words: str):
        words_list: list = words.split(",")
        addWordsToBlacklist(words_list)
        placeholders = {self.configManager.getBlacklistWordsPlaceholder(): words_list}
        await sendResponse(interaction, self.configManager.getAddedWordsToBlacklistKey(), placeholders)


    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="deafen")
    @app_commands.describe(member=configManager.getMentionMemberArg(), reason=configManager.getReasonArg())
    async def deafen(self, interaction: discord.Interaction, member: str, reason: str = ""):
        try:
            member: discord.Member = getMember(interaction, get_member_id_from_mention(member))
            await member.edit(deafen=True, reason=reason)
            placeholders = {self.configManager.getUsernamePlaceholder(): member.name,
                            self.configManager.getReasonPlaceholder(): reason}

            await sendResponse(interaction, self.configManager.getDeafenKey(), placeholders)

        except Exception as e:
            placeholders = {self.configManager.getErrorPlaceholder(): e}
            await sendResponse(interaction, self.configManager.getUnknownErrorKey(), placeholders)


    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="undeafen")
    @app_commands.describe(member=configManager.getMentionMemberArg(), reason=configManager.getReasonArg())
    async def undeafen(self, interaction: discord.Interaction, member: str, reason: str = ""):
        try:
            member: discord.Member = getMember(interaction, get_member_id_from_mention(member))
            await member.edit(deafen=False, reason=reason)
            placeholders = {self.configManager.getUsernamePlaceholder(): member.name,
                            self.configManager.getReasonPlaceholder(): reason}

            await sendResponse(interaction, self.configManager.getDeafenKey(), placeholders)

        except Exception as e:
            placeholders = {self.configManager.getErrorPlaceholder(): e}
            await sendResponse(interaction, self.configManager.getUnknownErrorKey(), placeholders)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="kick")
    @app_commands.describe(member=configManager.getMentionMemberArg(), reason=configManager.getReasonArg())
    async def kick(self, interaction: discord.Interaction, member: str, reason: str = ""):
        try:
            member = getMember(interaction, get_member_id_from_mention(member))
            await member.kick(reason=reason)
            placeholders = {configManager.getUsernamePlaceholder(): member.name,
                            configManager.getReasonPlaceholder(): reason}
            await sendResponse(interaction, self.configManager.getClearWarningsMemberKey(), placeholders)

        except Exception as e:
            placeholders = {self.configManager.getErrorPlaceholder(): e}
            await sendResponse(interaction, self.configManager.getUnknownErrorKey(), placeholders)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="move")
    @app_commands.describe(member=configManager.getMentionMemberArg(),
                           channel=configManager.getMentionVoiceChannelArg(),
                           reason=configManager.getReasonArg())
    async def move(self, interaction: discord.Interaction, member: str, channel: str, reason: str = ""):
        try:
            channel = getVoiceChannel(interaction, get_channel_id_from_mention(channel))
            member = getMember(interaction, get_member_id_from_mention(member))
            await member.move_to(channel, reason=reason)
            placeholders = {configManager.getUsernamePlaceholder(): member.name,
                            configManager.getChannelNamePlaceholder(): channel.name,
                            configManager.getReasonPlaceholder(): reason}
            await sendResponse(interaction, self.configManager.getMoveMemberToChannelKey(), placeholders)

        except Exception as e:
            placeholders = {self.configManager.getErrorPlaceholder(): e}
            await sendResponse(interaction, self.configManager.getUnknownErrorKey(), placeholders)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="clear")
    @app_commands.describe(number=configManager.getNumberArg())
    async def clear(self, interaction: discord.Interaction, number: str):
        try:
            await interaction.channel.purge(limit=int(number))

            placeholders = {configManager.getRemoveMessagesKey(): number}
            await sendResponse(interaction, self.configManager.getMoveMemberToChannelKey(), placeholders)

        except Exception as e:
            placeholders = {self.configManager.getErrorPlaceholder(): e}
            await sendResponse(interaction, self.configManager.getUnknownErrorKey(), placeholders)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="say")
    @app_commands.describe(message=configManager.getEnterMessageArg())
    async def say(self, interaction: discord.Interaction, message: str):
        try:
            placeholders = {configManager.getMessagePlaceholder(): message}
            await sendResponse(interaction, self.configManager.getSayMessageKey(), placeholders)

        except Exception as e:
            placeholders = {self.configManager.getErrorPlaceholder(): e}
            await sendResponse(interaction, self.configManager.getUnknownErrorKey(), placeholders)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="timeout")
    @app_commands.describe(member=configManager.getMentionMemberArg(),
                           until=configManager.getDatetimeArg(), reason=configManager.getReasonArg())
    async def timeout(self, interaction: discord.Interaction, member: str, until: str, reason: str = ""):
        try:
            member = getMember(interaction, get_member_id_from_mention(member))
            await member.timeout(datetime.datetime.strptime(until, "YYYY-MM-DDTHH:MM:SS"), reason=reason)

            placeholders = {configManager.getUsernamePlaceholder(): member.name,
                            configManager.getReasonPlaceholder(): reason,
                            configManager.getDatetimePlaceholder(): until}
            await sendResponse(interaction, self.configManager.getTimeoutMemberKey(), placeholders)

        except Exception as e:
            placeholders = {self.configManager.getErrorPlaceholder(): e}
            await sendResponse(interaction, self.configManager.getUnknownErrorKey(), placeholders)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="removetimeout")
    @app_commands.describe(member=configManager.getMentionMemberArg())
    async def removetimeout(self, interaction: discord.Interaction, member: str):
        try:
            member = getMember(interaction, get_member_id_from_mention(member))
            await member.edit(timed_out_until=None)

            placeholders = {configManager.getUsernamePlaceholder(): member.name}
            await sendResponse(interaction, self.configManager.getRemoveTimeoutMemberKey(), placeholders)

        except Exception as e:
            placeholders = {self.configManager.getErrorPlaceholder(): e}
            await sendResponse(interaction, self.configManager.getUnknownErrorKey(), placeholders)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="slowmode")
    @app_commands.describe(seconds=configManager.getNumberArg())
    async def slowmode(self, interaction: discord.Interaction, seconds: str):
        # ctx.channel.edit(slowmode_delay=seconds)
        try:
            await interaction.channel.edit(slowmode_delay=int(seconds))

            placeholders = {configManager.getChannelNamePlaceholder(): interaction.channel.name,
                            configManager.getNumberPlaceholder(): seconds}
            await sendResponse(interaction, self.configManager.getSlowmodeChannelKey(), placeholders)

        except Exception as e:
            placeholders = {self.configManager.getErrorPlaceholder(): e}
            await sendResponse(interaction, self.configManager.getUnknownErrorKey(), placeholders)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="vmute")
    @app_commands.describe(member=configManager.getMentionMemberArg())
    async def vmute(self, interaction: discord.Interaction, member: str):
        try:
            member = getMember(interaction, get_member_id_from_mention(member))
            await member.edit(mute=True)

            placeholders = {configManager.getUsernamePlaceholder(): member.name}
            await sendResponse(interaction, self.configManager.getVoiceMuteMemberKey(), placeholders)

        except Exception as e:
            placeholders = {self.configManager.getErrorPlaceholder(): e}
            await sendResponse(interaction, self.configManager.getUnknownErrorKey(), placeholders)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="vunmute")
    @app_commands.describe(member=configManager.getMentionMemberArg())
    async def vunmute(self, interaction: discord.Interaction, member: str):
        try:
            member = getMember(interaction, get_member_id_from_mention(member))
            await member.edit(mute=False)

            placeholders = {configManager.getUsernamePlaceholder(): member.name}
            await sendResponse(interaction, self.configManager.getVoiceUnmuteMemberKey(), placeholders)

        except Exception as e:
            placeholders = {self.configManager.getErrorPlaceholder(): e}
            await sendResponse(interaction, self.configManager.getUnknownErrorKey(), placeholders)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="vkick")
    @app_commands.describe(member=configManager.getMentionMemberArg())
    async def vkick(self, interaction: discord.Interaction, member: str):
        try:
            member = getMember(interaction, get_member_id_from_mention(member))
            await member.move_to(None)

            placeholders = {configManager.getUsernamePlaceholder(): member.name}
            await sendResponse(interaction, self.configManager.getKickFromVoiceKey(), placeholders)

        except Exception as e:
            placeholders = {self.configManager.getErrorPlaceholder(): e}
            await sendResponse(interaction, self.configManager.getUnknownErrorKey(), placeholders)