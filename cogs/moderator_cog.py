from __future__ import annotations

import datetime

import asyncio
import discord.errors
from cogs.ext.utils import *


async def setup(bot: commands.Bot):
    # guilds=[discord.Object(id=....)]
    await bot.add_cog(ModeratorCog(bot))


class ModeratorCog(commands.Cog, name="Moderator"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(description=configManager.getCommandArgDescription("avatar", "description"))
    @app_commands.describe(member=configManager.getCommandArgDescription("avatar", configManager.getMentionMemberKey()))
    async def avatar(self, interaction: discord.Interaction, member: str = ""):
        if await handleRestricted(self.bot, interaction, "avatar"):
            return

        if member == "":
            member: discord.Member = interaction.user
        else:
            member: discord.Member = getMember(interaction, get_member_id_from_mention(member))

        if member is None:
            await handleInvalidMember(interaction, "avatar")
            return

        await handleMessage(self.bot, interaction, "avatar",
                            placeholders={configManager.getUsernamePlaceholder(): member.name,
                                          configManager.getAvatarUrlPlaceholder(): member.avatar.url})

    @app_commands.command(description=configManager.getCommandArgDescription("invite", "description"))
    @app_commands.describe(bot_id=configManager.getCommandArgDescription("invite", configManager.getMemberIDKey()),
                           permissions=configManager.getCommandArgDescription("invite", configManager.getNumberKey()))
    async def invite(self, interaction: discord.Interaction, bot_id: str, permissions: str):
        if await handleRestricted(self.bot, interaction, "invite"):
            return

        if not bot_id.isdigit() or not permissions.isdigit():
            await handleMessage(self.bot, interaction, "invite", error_name=configManager.getInvalidArgsKey(),
                                placeholders={
                                    configManager.getErrorPlaceholder():
                                        configManager.getCommandMessages("invite", configManager.getNumberKey())})
            return
        # https://discord.com/oauth2/authorize?client_id=1223731465309917204&scope=applications.commands%20bot&permissions=8
        await handleMessage(self.bot, interaction, "invite", placeholders={
            configManager.getInvitePlaceholder(): "https://discord.com/oauth2/authorize?client_id=" +
                                                  bot_id + "&scope=applications.commands%20bot&permissions=" +
                                                  permissions})

    @app_commands.command(description=configManager.getCommandArgDescription("ping", "description"))
    async def ping(self, interaction: discord.Interaction):
        if await handleRestricted(self.bot, interaction, "ping"):
            return

        await handleMessage(self.bot, interaction, "ping",
                            placeholders={configManager.getBotLatencyPlaceholder(): str(round(self.bot.latency, 1))})

    @app_commands.command(description=configManager.getCommandArgDescription("addrole", "description"))
    @app_commands.describe(
        member=configManager.getCommandArgDescription("addrole", configManager.getMentionMemberKey()),
        role=configManager.getCommandArgDescription("addrole", configManager.getMentionRoleKey()),
        reason=configManager.getCommandArgDescription("addrole", configManager.getReasonKey()))
    async def addrole(self, interaction: discord.Interaction, member: str, role: str, reason: str = ""):
        if await handleRestricted(self.bot, interaction, "addrole"):
            return

        member_obj: discord.Member = getMember(interaction, get_member_id_from_mention(member))
        if member_obj is None:
            await handleInvalidMember(self.bot, interaction, "addrole")
            return

        role_obj = getRole(interaction, get_role_id_from_mention(role))
        if role_obj is None:
            await handleInvalidRole(self.bot, interaction, "addrole")
            return

        try:
            await member_obj.add_roles(role_obj, reason=reason)

            await handleMessage(self.bot, interaction, "addrole",
                                placeholders={configManager.getRoleNamePlaceholder(): role_obj.name,
                                              configManager.getReasonPlaceholder(): reason})
        except Exception as e:
            await handleErrors(self.bot, interaction, "addrole", e)

    @app_commands.command(description=configManager.getCommandArgDescription("removerole", "description"))
    @app_commands.describe(
        member=configManager.getCommandArgDescription("removerole", configManager.getMentionMemberKey()),
        role=configManager.getCommandArgDescription("removerole", configManager.getMentionRoleKey()),
        reason=configManager.getCommandArgDescription("removerole", configManager.getReasonKey()))
    async def removerole(self, interaction: discord.Interaction, member: str, role: str, reason: str = ""):
        if await handleRestricted(self.bot, interaction, "removerole"):
            return

        member_obj: discord.Member = getMember(interaction, get_member_id_from_mention(member))
        if member_obj is None:
            await handleInvalidMember(self.bot, interaction, "removerole")
            return

        role_obj = getRole(interaction, get_role_id_from_mention(role))
        if role_obj is None:
            await handleInvalidRole(self.bot, interaction, "removerole")
            return

        try:
            await member_obj.remove_roles(role_obj, reason=reason)

            await handleMessage(self.bot, interaction, "removerole",
                                placeholders={configManager.getRoleNamePlaceholder(): role_obj.name,
                                              configManager.getReasonPlaceholder(): reason})
        except Exception as e:
            await handleErrors(self.bot, interaction, "removerole", e)

    @app_commands.command(description=configManager.getCommandArgDescription("ban", "description"))
    @app_commands.describe(member=configManager.getCommandArgDescription("ban", configManager.getMentionMemberKey()),
                           reason=configManager.getCommandArgDescription("ban", configManager.getReasonKey()),
                           duration=configManager.getCommandArgDescription("ban", configManager.getNumberKey()),
                           unban_reason=configManager.getCommandArgDescription("ban", configManager.getReasonKey()))
    async def ban(self, interaction: discord.Interaction, member: str, reason: str = "", duration: int = -1,
                  unban_reason: str = ""):
        if await handleRestricted(self.bot, interaction, "ban"):
            return

        member = getMember(interaction, get_member_id_from_mention(member))
        if member is None:
            await handleInvalidMember(self.bot, interaction, "ban")
            return

        try:
            await member.ban(reason=reason)

            await handleMessage(self.bot, interaction, "ban",
                                placeholders={configManager.getUsernamePlaceholder(): member.name,
                                              configManager.getReasonPlaceholder(): reason})
            if duration > 0:
                await asyncio.sleep(duration)
                await member.unban(reason=unban_reason)

        except Exception as e:
            await handleErrors(self.bot, interaction, "ban", e)

    @app_commands.command(description=configManager.getCommandArgDescription("unban", "description"))
    @app_commands.describe(member=configManager.getCommandArgDescription("unban", configManager.getMentionMemberKey()),
                           reason=configManager.getCommandArgDescription("unban", configManager.getReasonKey()))
    async def unban(self, interaction: discord.Interaction, member: str, reason: str):
        if await handleRestricted(self.bot, interaction, "unban"):
            return

        member: discord.Member | None = getMember(interaction, get_member_id_from_mention(member))
        if member is None:
            await handleInvalidMember(self.bot, interaction, "unban")
            return

        try:
            await member.unban(reason=reason)
        except Exception as e:
            await handleErrors(self.bot, interaction, "unban", e)


    @app_commands.command(description=configManager.getCommandArgDescription("blacklist", "description"))
    @app_commands.describe(
        words=configManager.getCommandArgDescription("blacklist", configManager.getBlacklistWordsKey()))
    async def blacklist(self, interaction: discord.Interaction, words: str):
        if await handleRestricted(self.bot, interaction, "blacklist"):
            return

        try:
            words_list: list = words.split(",")
            for i in range(len(words_list)):
                if len(words_list[i].replace(" ", "")) == 0:
                    words_list.pop(i)

            addWordsToBlacklist(words_list)
            await handleMessage(self.bot, interaction, "blacklist",
                                placeholders={configManager.getBlacklistWordsPlaceholder(): words_list})

        except Exception as e:
            await handleErrors(self.bot, interaction, "blacklist", e)

    @app_commands.command(description=configManager.getCommandArgDescription("removeblacklist", "description"))
    @app_commands.describe(
        words=configManager.getCommandArgDescription("removeblacklist", configManager.getBlacklistWordsKey()))
    async def removeblacklist(self, interaction: discord.Interaction, words: str):
        if await handleRestricted(self.bot, interaction, "removeblacklist"):
            return

        try:
            words_list: list = words.split(",")
            for i in range(len(words_list)):
                if len(words_list[i].replace(" ", "")) == 0:
                    words_list.pop(i)

            removeWordsFromBlacklist(words_list)
            await handleMessage(self.bot, interaction, "removeblacklist",
                                placeholders={configManager.getBlacklistWordsPlaceholder(): words_list})

        except Exception as e:
            await handleErrors(self.bot, interaction, "removeblacklist", e)

    @commands.Cog.listener()
    async def on_message(self, message: discord.message.Message):
        if message.author.id != self.bot.user.id:
            for word in configManager.getBlacklistedWords():
                if word in message.content:
                    await message.delete()
                    return

            handleUserLevelingOnMessage(message.author)

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        return

    @app_commands.command(description=configManager.getCommandArgDescription("deafen", "description"))
    @app_commands.describe(member=configManager.getCommandArgDescription("deafen", configManager.getMentionMemberKey()),
                           reason=configManager.getCommandArgDescription("deafen", configManager.getReasonKey()))
    async def deafen(self, interaction: discord.Interaction, member: str, reason: str = ""):
        if await handleRestricted(self.bot, interaction, "deafen"):
            return

        member: discord.Member = getMember(interaction, get_member_id_from_mention(member))
        if member is None:
            await handleInvalidMember(self.bot, interaction, "deafen")
            return

        try:
            await member.edit(deafen=True, reason=reason)
            await handleMessage(self.bot, interaction, "deafen",
                                placeholders={configManager.getUsernamePlaceholder(): member.name,
                                              configManager.getReasonPlaceholder(): reason})

        except Exception as e:
            await handleErrors(self.bot, interaction, "deafen", e)

    @app_commands.command(description=configManager.getCommandArgDescription("undeafen", "description"))
    @app_commands.describe(
        member=configManager.getCommandArgDescription("undeafen", configManager.getMentionMemberKey()),
        reason=configManager.getCommandArgDescription("undeafen", configManager.getReasonKey()))
    async def undeafen(self, interaction: discord.Interaction, member: str, reason: str = ""):
        if await handleRestricted(self.bot, interaction, "undeafen"):
            return

        member: discord.Member = getMember(interaction, get_member_id_from_mention(member))
        if member is None:
            await handleInvalidMember(self.bot, interaction, "undeafen")
            return

        try:
            await member.edit(deafen=False, reason=reason)
            await handleMessage(self.bot, interaction, "undeafen",
                                placeholders={configManager.getUsernamePlaceholder(): member.name,
                                              configManager.getReasonPlaceholder(): reason})

        except Exception as e:
            await handleErrors(self.bot, interaction, "undeafen", e)

    @app_commands.command(description=configManager.getCommandArgDescription("kick", "description"))
    @app_commands.describe(member=configManager.getCommandArgDescription("kick", configManager.getMentionMemberKey()),
                           reason=configManager.getCommandArgDescription("kick", configManager.getReasonKey()))
    async def kick(self, interaction: discord.Interaction, member: str, reason: str = ""):
        if await handleRestricted(self.bot, interaction, "kick"):
            return

        member = getMember(interaction, get_member_id_from_mention(member))
        if member is None:
            await handleInvalidMember(self.bot, interaction, "kick")
            return

        try:
            await member.kick(reason=reason)
            await handleMessage(self.bot, interaction, "kick",
                                placeholders={configManager.getUsernamePlaceholder(): member.name,
                                              configManager.getReasonPlaceholder(): reason})

        except Exception as e:
            await handleErrors(self.bot, interaction, "kick", e)

    @app_commands.command(description=configManager.getCommandArgDescription("move", "description"))
    @app_commands.describe(
        member_mention=configManager.getCommandArgDescription("move", configManager.getMentionMemberKey()),
        channel_mention=configManager.getCommandArgDescription("move",
                                                               configManager.getMentionVoiceChannelKey()),
        reason=configManager.getCommandArgDescription("move", configManager.getReasonKey()))
    async def move(self, interaction: discord.Interaction, member_mention: str, channel_mention: str, reason: str = ""):
        if await handleRestricted(self.bot, interaction, "move"):
            return

        channel = getVoiceChannel(interaction, get_channel_id_from_mention(channel_mention))
        if channel is None:
            await handleInvalidChannels(self.bot, interaction, "move")
            return

        member = getMember(interaction, get_member_id_from_mention(member_mention))
        if member is None:
            await handleInvalidMember(self.bot, interaction, "move")
            return

        try:
            await member.move_to(channel, reason=reason)
            await handleMessage(self.bot, interaction, "move",
                                placeholders={configManager.getUsernamePlaceholder(): member.name,
                                              configManager.getChannelNamePlaceholder(): channel.name,
                                              configManager.getReasonPlaceholder(): reason})

        except Exception as e:
            await handleErrors(self.bot, interaction, "move", e)

    @app_commands.command(description=configManager.getCommandArgDescription("clear", "description"))
    @app_commands.describe(number=configManager.getCommandArgDescription("clear", configManager.getNumberKey()))
    async def clear(self, interaction: discord.Interaction, number: str):
        if await handleRestricted(self.bot, interaction, "clear"):
            return

        try:
            await interaction.channel.purge(limit=int(number))
            await handleMessage(self.bot, interaction, "clear",
                                placeholders={configManager.getRemoveMessagesKey(): number})

        except Exception as e:
            await handleErrors(self.bot, interaction, "clear", e)

    @app_commands.command(description=configManager.getCommandArgDescription("say", "description"))
    @app_commands.describe(message=configManager.getCommandArgDescription("clear", configManager.getEnterMessageKey()))
    async def say(self, interaction: discord.Interaction, message: str):
        if await handleRestricted(self.bot, interaction, "say"):
            return

        try:
            await handleMessage(self.bot, interaction, "say",
                                placeholders={configManager.getMessagePlaceholder(): message})

        except Exception as e:
            await handleErrors(self.bot, interaction, "say", e)

    @app_commands.command(description=configManager.getCommandArgDescription("timeout", "description"))
    @app_commands.describe(
        member=configManager.getCommandArgDescription("timeout", configManager.getMentionMemberKey()),
        until=configManager.getCommandArgDescription("timeout", configManager.getDatetimeKey()),
        reason=configManager.getCommandArgDescription("timeout", configManager.getReasonKey()))
    async def timeout(self, interaction: discord.Interaction, member: str, until: str, reason: str = ""):
        if await handleRestricted(self.bot, interaction, "timeout"):
            return

        member = getMember(interaction, get_member_id_from_mention(member))
        if member is None:
            await handleInvalidMember(self.bot, interaction, "timeout")
            return

        try:
            await member.timeout(datetime.datetime.strptime(until, "YYYY-MM-DDTHH:MM:SS"), reason=reason)
            await handleMessage(self.bot, interaction, "timeout",
                                placeholders={configManager.getUsernamePlaceholder(): member.name,
                                              configManager.getReasonPlaceholder(): reason,
                                              configManager.getDatetimePlaceholder(): until})

        except Exception as e:
            await handleErrors(self.bot, interaction, "timeout", e)

    @app_commands.command(description=configManager.getCommandArgDescription("removetimeout", "description"))
    @app_commands.describe(
        member=configManager.getCommandArgDescription("removetimeout", configManager.getMentionMemberKey()))
    async def removetimeout(self, interaction: discord.Interaction, member: str):
        if await handleRestricted(self.bot, interaction, "removetimeout"):
            return

        member = getMember(interaction, get_member_id_from_mention(member))
        if member is None:
            await handleInvalidMember(self.bot, interaction, "removetimeout")
            return

        try:
            await member.edit(timed_out_until=None)
            await handleMessage(self.bot, interaction, "removetimeout",
                                placeholders={configManager.getUsernamePlaceholder(): member.name})

        except Exception as e:
            await handleErrors(self.bot, interaction, "removetimeout", e)

    @app_commands.command(description=configManager.getCommandArgDescription("slowmode", "description"))
    @app_commands.describe(seconds=configManager.getCommandArgDescription("slowmode", configManager.getNumberKey()))
    async def slowmode(self, interaction: discord.Interaction, seconds: str):
        # ctx.channel.edit(slowmode_delay=seconds)

        if await handleRestricted(self.bot, interaction, "slowmode"):
            return

        if not seconds.isdigit():
            await handleInvalidArg(self.bot, interaction, "slowmode")
            return

        try:
            await interaction.channel.edit(slowmode_delay=int(seconds))
            await handleMessage(self.bot, interaction, "slowmode",
                                placeholders={configManager.getChannelNamePlaceholder(): interaction.channel.name,
                                              configManager.getNumberPlaceholder(): seconds})

        except Exception as e:
            await handleErrors(self.bot, interaction, "slowmode", e)

    @app_commands.command(description=configManager.getCommandArgDescription("vmute", "description"))
    @app_commands.describe(member=configManager.getCommandArgDescription("vmute", configManager.getMentionMemberKey()))
    async def vmute(self, interaction: discord.Interaction, member: str):
        if await handleRestricted(self.bot, interaction, "vmute"):
            return

        member = getMember(interaction, get_member_id_from_mention(member))
        if member is None:
            await handleInvalidMember(self.bot, interaction, "vmute")
            return

        try:
            await member.edit(mute=True)
            await handleMessage(self.bot, interaction, "vmute",
                                placeholders={configManager.getUsernamePlaceholder(): member.name})

        except Exception as e:
            await handleErrors(self.bot, interaction, "vmute", e)

    @app_commands.command(description=configManager.getCommandArgDescription("vunmute", "description"))
    @app_commands.describe(
        member=configManager.getCommandArgDescription("vunmute", configManager.getMentionMemberKey()))
    async def vunmute(self, interaction: discord.Interaction, member: str):
        if await handleRestricted(self.bot, interaction, "vunmute"):
            return

        member = getMember(interaction, get_member_id_from_mention(member))
        if member is None:
            await handleInvalidMember(self.bot, interaction, "vunmute")
            return

        try:
            await member.edit(mute=False)
            await handleMessage(self.bot, interaction, "vunmute",
                                placeholders={configManager.getUsernamePlaceholder(): member.name})
        except Exception as e:
            await handleErrors(self.bot, interaction, "vunmute", e)

    @app_commands.command(description=configManager.getCommandArgDescription("vkick", "description"))
    @app_commands.describe(member=configManager.getCommandArgDescription("vkick", configManager.getMentionMemberKey()))
    async def vkick(self, interaction: discord.Interaction, member: str):
        if await handleRestricted(self.bot, interaction, "vkick"):
            return

        member = getMember(interaction, get_member_id_from_mention(member))
        if member is None:
            await handleInvalidMember(self.bot, interaction, "vkick")
            return

        try:
            await member.move_to(None)
            await handleMessage(self.bot, interaction, "vkick",
                                placeholders={configManager.getUsernamePlaceholder(): member.name})

        except Exception as e:
            await handleErrors(self.bot, interaction, "vkick", e)

    @app_commands.command(description=configManager.getCommandArgDescription("dm", "description"))
    @app_commands.describe(member=configManager.getCommandArgDescription("dm", configManager.getMentionMemberKey()),
                           message=configManager.getCommandArgDescription("dm", configManager.getEnterMessageKey()))
    async def dm(self, interaction: discord.Interaction, message: str, member: str = ""):
        if await handleRestricted(self.bot, interaction, "dm"):
            return

        if len(message.replace(" ", "")) == 0:
            await handleInvalidArg(self.bot, interaction, "dm")
            return

        if member == "":
            member: discord.Member = interaction.user
        else:
            member: discord.Member = getMember(interaction, get_member_id_from_mention(member))

        if member is None:
            await handleInvalidMember(self.bot, interaction, "dm")
            return

        await handleMessage(self.bot, interaction, "dm",
                            placeholders={configManager.getUsernamePlaceholder(): interaction.user.name,
                                          configManager.getMessagePlaceholder(): message}, dm_user=member)

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        return