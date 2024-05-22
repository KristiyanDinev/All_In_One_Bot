from __future__ import annotations

from typing import List

import asyncio
import discord
from discord.ext import commands
from discord import Member, Role

from cogs.ext.config_manager import ConfigManager

configManager = ConfigManager("configs/config", "configs/messages",
                              "configs/warnings",
                              "configs/commands", "configs/levels")


def getMember(interaction: discord.Interaction, memberId: int) -> Member | None:
    if memberId == 0:
        return None
    return interaction.client.get_user(memberId)


def getMemberGuild(guild: discord.Guild, memberId: int) -> Member | None:
    if memberId == 0:
        return None
    return guild.get_member(memberId)


def getRoleIdFromMention(roleMention: str) -> int:
    try:
        return int(roleMention.replace("<@&", "")[:-1]) if "<@" in roleMention else int(roleMention)
    except Exception:
        return 0


def getMemberIdFromMention(memberMention: str) -> int:
    try:
        return int(memberMention.replace("<@", "")[:-1]) if "<@" in memberMention else int(memberMention)
    except Exception:
        return 0


def getRole(interaction: discord.Interaction, roleId: int) -> None | discord.Role:
    if roleId == 0:
        return None
    return interaction.client.get_role(roleId)


def getChannelIdFromMention(channelMention: str) -> int:
    try:
        return int(channelMention.replace("<#", "")[:-1]) if "<#" in channelMention else int(channelMention)
    except Exception:
        return 0


def getVoiceChannel(interaction: discord.Interaction, channelId: int) -> None | discord.VoiceChannel:
    if channelId == 0:
        return None
    channel = interaction.client.get_channel(channelId)
    return channel if type(channel) == discord.VoiceChannel else None


def addWordsToBlacklist(words: list):
    configManager.getBlacklistedWords().extend(words)
    configManager.updateBlacklistWords(configManager.getBlacklistedWords())
    configManager.saveConfigJSON()


def removeWordsFromBlacklist(words: list):
    configManager.updateBlacklistWords([i for i in configManager.getBlacklistedWords() if i not in words])
    configManager.saveConfigJSON()


def getRoleIdFromRoles(roles: List[Role]) -> list:
    userRolesId = []
    for r in roles:
        if r.name == "@everyone":
            continue
        userRolesId.append(r.id)
    return userRolesId


def getUserWarningLevel(user: discord.Member) -> int:
    lastIndex = 0
    for i in range(1, configManager.getWarningLevels() + 1):
        warningData: dict = configManager.getWarningDataForLevel(i)
        if len(warningData) == 0:
            continue

        rolesId: list | None = warningData.get("roles_id", None)
        userRolesId = getRoleIdFromRoles(user.roles)
        if rolesId is not None:
            rolesId.sort()
            userRolesId.sort()

            if rolesId == userRolesId and lastIndex < i:
                lastIndex = i
    return lastIndex


def anyRolesContains(roles_id: list, roles_id2: list) -> bool:
    for role_id in roles_id:
        if role_id in roles_id2:
            return True
    return False


def allRolesContains(roles_id: list, roles_id2: list) -> bool:
    for role_id in roles_id:
        if role_id not in roles_id2:
            return False
    return True if len(roles_id) > 0 else False


def getWarningRolesFromLevel(interaction: discord.Interaction, level: int) -> List[Role]:
    warning_data: dict = configManager.getWarningDataForLevel(level)

    warningRoles = []
    if len(warning_data) == 0:
        return warningRoles

    roles_id: list | None = warning_data.get("roles_id", None)

    if roles_id is not None:
        for r_id in roles_id:
            r = interaction.guild.get_role(r_id)
            if r is not None:
                warningRoles.append(r)
    return warningRoles


def isUserRestricted(interaction: discord.Interaction, commandName: str) -> str:
    res = configManager.getCommandRestrictions(commandName)
    reason = ""
    if res.get("all", None) is not None:
        if res.get("all"):
            return reason
        else:
            reason += "all;"

    usersId: list | None = res.get("users_id", None)
    if usersId is not None and interaction.user.id not in usersId:
        reason += "user id;"

    userRoleId: list = getRoleIdFromRoles(interaction.user.roles)
    anyRolesId: list | None = res.get("any_roles_id", None)
    if anyRolesId is not None and anyRolesContains(anyRolesId, userRoleId):
        reason += "any roles;"

    allRolesId: list | None = res.get("all_roles_id", None)
    if allRolesId is not None and not allRolesContains(userRoleId, allRolesId):
        reason += "all roles;"

    channelsId = res.get("channels_id", None)
    if channelsId is not None and interaction.channel.id not in channelsId:
        reason += "channel id;"

    return reason


def isUserRestrictedCtx(ctx: discord.ext.commands.context.Context, commandName: str) -> str:
    res = configManager.getCommandRestrictions(commandName)
    restrictedReason = ""
    if res.get("all", None) is not None:
        if res.get("all"):
            return restrictedReason
        else:
            restrictedReason += "all;"

    usersId: list | None = res.get("users_id", None)
    if usersId is not None and ctx.author.id not in usersId:
        restrictedReason += "user id;"

    userRoleId: list = getRoleIdFromRoles(ctx.author.roles)
    anyRolesId: list | None = res.get("any_roles_id", None)
    if anyRolesId is not None and anyRolesContains(anyRolesId, userRoleId):
        restrictedReason += "any roles;"

    allRolesId: list | None = res.get("all_roles_id", None)
    if allRolesId is not None and not allRolesContains(userRoleId, allRolesId):
        restrictedReason += "all roles;"

    channelsId = res.get("channels_id", None)
    if channelsId is not None and ctx.channel.id not in channelsId:
        restrictedReason += "channel id;"

    return restrictedReason


def separateThread(loop, func, *args):
    asyncio.run_coroutine_threadsafe(func(*args), loop)


async def giveRoleToUser(user: discord.User, role: discord.Role, reason: str = "") -> bool:
    try:
        await user.add_roles(role, reason=reason)
        return True
    except Exception:
        return False


async def removeRoleToUser(user: discord.User, role: discord.Role, reason: str = "") -> bool:
    try:
        await user.remove_roles(role, reason=reason)
        return True
    except Exception:
        return False


async def createRoleWithDisplayIcon(roleData: dict, guild: discord.Guild) -> discord.Role | None:
    try:
        role: discord.Role = await guild.create_role(reason=roleData.get("reason", ""),
                                                     name=roleData.get("name", "No Name Given"),
                                                     display_icon=roleData.get("display_icon"),
                                                     color=getColor(str(roleData.get("color", ""))),
                                                     mentionable=bool(roleData.get("mentionable", True)),
                                                     hoist=bool(roleData.get("hoist", True)),
                                                     permissions=getDiscordPermission(
                                                         dict(roleData.get("permissions", {}))))
        pos: str = str(roleData.get("position", ""))
        if pos.isdigit():
            await role.edit(position=int(pos))

        for usersId in list(roleData.get("users", [])):
            if not str(usersId).isdigit():
                continue
            member: discord.Member | None = guild.get_member(int(usersId))
            if member is not None:
                await giveRoleToUser(member, role, str(roleData.get("give_reason", "")))
    except Exception:
        return None


async def createRoleNoDisplayIcon(roleData: dict, guild: discord.Guild) -> discord.Role | None:
    try:
        role: discord.Role = await guild.create_role(reason=roleData.get("reason", ""),
                                                     name=roleData.get("name", "No Name Given"),
                                                     color=getColor(str(roleData.get("color", ""))),
                                                     mentionable=bool(roleData.get("mentionable", True)),
                                                     hoist=bool(roleData.get("hoist", True)),
                                                     permissions=getDiscordPermission(
                                                         dict(roleData.get("permissions", {}))))
        pos: str = str(roleData.get("position", ""))
        if pos.isdigit():
            await role.edit(position=int(pos))

        for usersId in list(roleData.get("users", [])):
            if not str(usersId).isdigit():
                continue
            member: discord.Member | None = guild.get_member(int(usersId))
            if member is not None:
                await giveRoleToUser(member, role, str(roleData.get("give_reason", "")))
        return role
    except Exception:
        return None


async def deleteRole(roleData: dict, guild: discord.Guild) -> List[discord.Role] | None:
    roles = getRoles(roleData, guild)
    deleted = []
    reason = str(roleData.get("reason", ""))
    for r in roles:
        try:
            await r.delete(reason=reason)
            deleted.append(r)
        except Exception:
            continue
    return deleted


def getRoles(roleData: dict, guild: discord.Guild) -> list:
    try:
        roleId: str = str(roleData.get("id", ""))
        roleName: str = str(roleData.get("name", ""))
        roles = set()
        if roleId.isdigit():
            # search by id
            roles.add(guild.get_role(int(roleId)))

        if len(roleName.replace(" ", "")) > 0 and roleName != "@everyone":
            # search by name
            if roleName == "*":
                for r in guild.roles:
                    if r.name != "@everyone":
                        roles.add(r)
            else:
                for r in guild.roles:
                    if r.name != "@everyone" and r.name == roleName:
                        roles.add(r)
        return list(roles)
    except Exception:
        return []


async def banUser(member: discord.Member, reason: str = "") -> bool:
    try:
        await member.ban(reason=reason)
        return True
    except Exception:
        return False


async def unbanUser(member: discord.Member, reason: str = "") -> bool:
    try:
        await member.unban(reason=reason)
        return True
    except Exception:
        return False


async def kickUser(member: discord.Member, reason: str = "") -> bool:
    try:
        await member.kick(reason=reason)
        return True
    except Exception:
        return False


async def addRole(member: discord.Member, role: discord.Role, reason: str = "") -> bool:
    try:
        await member.add_roles(role, reason=reason)
    except Exception:
        return False


async def removeRole(member: discord.Member, role: discord.Role, reason: str = "") -> bool:
    try:
        await member.remove_roles(role, reason=reason)
        return True
    except Exception:
        return False


async def timeoutUser(member: discord.Member, datetime_zone, reason: str = "") -> bool:
    try:
        await member.timeout(datetime_zone, reason=reason)
        return True
    except Exception:
        return False


async def removeTimeoutUser(member: discord.Member, reason: str = "") -> bool:
    try:
        await member.edit(timed_out_until=None, reason=reason)
        return True
    except Exception:
        return False


async def userDeafen(member: discord.Member, status: bool, reason: str = "") -> bool:
    try:
        await member.edit(deafen=status, reason=reason)
        return True
    except Exception:
        return False


async def userMute(member: discord.Member, status: bool, reason: str = "") -> bool:
    try:
        await member.edit(mute=status, reason=reason)
        return True
    except Exception:
        return False


def getRoleData(role: discord.Role) -> dict:
    roleData = dict()
    roleData["name"] = role.name
    roleData["color"] = role.color
    roleData["display_icon"] = role.display_icon
    roleData["mentionable"] = role.mentionable
    roleData["hoist"] = role.hoist
    roleData["position"] = role.position
    roleData["permissions"] = {perm: getattr(role.permissions, perm)
                               for perm, value in discord.Permissions.VALID_FLAGS.items()}
    users = []
    for member in role.members:
        users.append(member.id)
    roleData["users"] = users
    return roleData


async def deleteRole(role: discord.Role, reason: str = "") -> bool:
    try:
        await role.delete(reason=reason)
        return True
    except Exception:
        return False


async def editRole(roleData: dict, role: discord.Role, guild: discord.Guild) -> bool:
    try:
        position: str | None = str(roleData.get("position", None))
        reason: str = str(roleData.get("reason", ""))
        if position is None or not position.isdigit():
            position = None
        try:
            await role.edit(name=str(roleData.get("new_name", "Edited Role")),
                            reason=reason,
                            color=getColor(str(roleData.get("color", ""))), hoist=bool(roleData.get("hoist", True)),
                            mentionable=bool(roleData.get("mentionable", True)), position=int(position),
                            permissions=getDiscordPermission(dict(roleData.get("permissions", {}))),
                            display_icon=roleData.get("display_icon", None))
        except Exception:
            try:
                await role.edit(name=str(roleData.get("new_name", "Edited Role")),
                                reason=str(roleData.get("reason", "")),
                                color=getColor(str(roleData.get("color", ""))), hoist=bool(roleData.get("hoist", True)),
                                mentionable=bool(roleData.get("mentionable", True)), position=int(position),
                                permissions=getDiscordPermission(dict(roleData.get("permissions", {}))))
            except Exception:
                return False

        if "users" in roleData.keys():
            users: list = list(roleData.get("users", []))
            for member in role.members:
                if member.id in users:
                    continue
                await removeRole(member, role, reason=reason)

            for userId in users:
                member: discord.Member | None = getMemberGuild(guild, userId)
                if member is None or memberHasRole(member, role):
                    continue
                await addRole(member, role, reason=reason)

        return True
    except Exception:
        return False


def getColor(color: str) -> discord.Color:
    try:
        return discord.Colour.random() if color == "random" or len(color) == 0 else discord.Color.from_str(color)
    except Exception:
        return discord.Color.red()


def getDiscordPermission(permissions: dict) -> discord.Permissions:
    return discord.Permissions(**permissions)


def memberHasRole(member: discord.Member, role: discord.Role) -> bool:
    return member.get_role(role.id) is not None


def getGuildData(guild: discord.Guild) -> dict:
    data = dict()
    data["name"] = guild.name
    data["banner"] = guild.banner
    data["id"] = guild.id
    data["afk_channel_id"] = guild.afk_channel.id if guild.afk_channel is not None else 0
    data["afk_timeout"] = guild.afk_timeout
    data["member_count"] = guild.member_count
    data["bitrate_limit"] = guild.bitrate_limit
    data["created_at"] = guild.created_at
    data["default_notifications"] = str(guild.default_notifications.name)
    data["description"] = guild.description if guild.description is not None else ""
    data["emoji_limit"] = guild.emoji_limit
    data["icon"] = guild.icon.__str__() if guild.icon is not None else ""
    data["widget_enabled"] = guild.widget_enabled
    data["verification_level"] = str(guild.verification_level.name)
    data["large"] = guild.large
    data["max_members"] = guild.max_members if guild.max_members is not None else 0
    data["max_presences"] = guild.max_presences if guild.max_presences is not None else 0
    data["max_stage_video_users"] = guild.max_stage_video_users if guild.max_stage_video_users is not None else 0
    data["max_video_channel_users"] = guild.max_video_channel_users if guild.max_video_channel_users is not None else 0
    data["mfa_level"] = str(guild.mfa_level.name)
    data["nsfw_level"] = str(guild.nsfw_level.name)
    data["owner_id"] = guild.owner.id
    data["owner_name"] = guild.owner.name
    data["preferred_locale"] = str(guild.preferred_locale.name)
    data["premium_progress_bar_enabled"] = guild.premium_progress_bar_enabled
    data["explicit_content_filter"] = str(guild.explicit_content_filter.name)
    data["premium_subscription_count"] = guild.premium_subscription_count
    data["premium_tier"] = guild.premium_tier
    data["public_updates_channel_name"] = guild.public_updates_channel.name \
        if guild.public_updates_channel is not None else ""
    data["rules_channel_name"] = guild.rules_channel.name if guild.rules_channel is not None else ""
    data["shard_id"] = guild.shard_id
    data["vanity_url"] = guild.vanity_url if guild.vanity_url is not None else ""
    data["vanity_url_code"] = guild.vanity_url_code if guild.vanity_url_code is not None else ""
    data["widget_channel_name"] = guild.widget_channel.name if guild.widget_channel is not None else ""
    data["filesize_limit"] = guild.filesize_limit
    data["safety_alerts_channel_name"] = guild.safety_alerts_channel.name \
        if guild.safety_alerts_channel is not None else ""
    data["sticker_limit"] = guild.sticker_limit
    data["unavailable"] = guild.unavailable
    data["system_channel_name"] = guild.system_channel.name if guild.system_channel is not None else ""
    data["chunked"] = guild.chunked
    return data


async def editGuild(guildData: dict, guild: discord.Guild, reason: str = "") -> bool:
    # TODO Finish this
    try:
        print(guildData.get("description"))
        print(guildData.get("icon"))
        print(guildData.get("banner"))
        await guild.edit(reason=reason, name=str(guildData.get("name", "ServerName")),
                         description=guildData.get("description"), icon=guildData.get("icon"),
                         banner=guildData.get("banner"))

        return True
    except Exception as e:
        print(e)
        return False
