from __future__ import annotations

from typing import List, Any, Mapping, Union
import requests as rq
import asyncio
import discord
from discord.ext import commands
from discord import Role

from cogs.ext.config_manager import ConfigManager

configManager = ConfigManager("configs/config", "configs/messages",
                              "configs/warnings",
                              "configs/commands", "configs/levels")


def getMemberGuild(guild: discord.Guild, memberId: int) -> discord.Member | None:
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


def getVoiceChannelGuild(guild: discord.Guild, channelId: int) -> discord.VoiceChannel | None:
    if channelId == 0:
        return None
    channel = guild.get_channel(channelId)
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

        for user in getUsers(roleData, guild):
            await giveRoleToUser(user, role, str(roleData.get("give_reason", "")))
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

        for user in getUsers(roleData, guild):
            await giveRoleToUser(user, role, str(roleData.get("give_reason", "")))
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
        roleId: str = str(roleData.get("role_id", ""))
        roleName: str = str(roleData.get("role_name", ""))
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


def getPermissionData(role: discord.Role) -> dict:
    return {perm: getattr(role.permissions, perm)
            for perm, value in discord.Permissions.VALID_FLAGS.items()}


def getRoleData(role: discord.Role) -> dict:
    roleData = dict()
    roleData["name"] = role.name
    roleData["color"] = role.color
    roleData["display_icon"] = role.display_icon
    roleData["mentionable"] = role.mentionable
    roleData["hoist"] = role.hoist
    roleData["position"] = role.position
    roleData["permissions"] = getPermissionData(role)
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
    data["icon_url"] = guild.icon.__str__() if guild.icon is not None else ""
    data["icon"] = rq.get(guild.icon.__str__()).content if guild.icon is not None else ""
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
    data["content_filter"] = str(guild.explicit_content_filter.name)
    data["premium_subscription_count"] = guild.premium_subscription_count
    data["premium_tier"] = guild.premium_tier
    data["public_updates_channel_name"] = guild.public_updates_channel.name \
        if guild.public_updates_channel is not None else ""
    data["public_updates_channel_id"] = guild.public_updates_channel.id \
        if guild.public_updates_channel is not None else 0
    data["rules_channel_name"] = guild.rules_channel.name if guild.rules_channel is not None else ""
    data["rules_channel_id"] = guild.rules_channel.id if guild.rules_channel is not None else 0
    data["shard_id"] = guild.shard_id
    data["vanity_url"] = guild.vanity_url if guild.vanity_url is not None else ""
    data["vanity_url_code"] = guild.vanity_url_code if guild.vanity_url_code is not None else ""
    data["widget_channel_name"] = guild.widget_channel.name if guild.widget_channel is not None else ""
    data["widget_channel_id"] = guild.widget_channel.id if guild.widget_channel is not None else 0
    data["filesize_limit"] = guild.filesize_limit
    data["safety_alerts_channel_name"] = guild.safety_alerts_channel.name \
        if guild.safety_alerts_channel is not None else ""
    data["safety_alerts_channel_id"] = guild.safety_alerts_channel.id \
        if guild.safety_alerts_channel is not None else ""
    data["sticker_limit"] = guild.sticker_limit
    data["unavailable"] = guild.unavailable
    data["system_channel_name"] = guild.system_channel.name if guild.system_channel is not None else ""
    data["system_channel_id"] = guild.system_channel.id if guild.system_channel is not None else 0
    data["chunked"] = guild.chunked
    data["splash_url"] = guild.splash.__str__() if guild.splash is not None else ""
    data["splash"] = rq.get(guild.splash.__str__()).content if guild.splash is not None else ""
    data["discovery_splash_url"] = guild.discovery_splash.__str__() if guild.splash is not None else ""
    data["discovery_splash"] = rq.get(guild.discovery_splash.__str__()).content if guild.splash is not None else ""
    data["system_channel_flags"] = {flag: getattr(guild.system_channel_flags, flag)
                                    for flag, value in discord.SystemChannelFlags.VALID_FLAGS.items()}
    data["guild_features"] = guild.features
    return data


async def editGuild(guildData: dict, guild: discord.Guild, reason: str = "") -> bool:
    success = False
    for key in guildData.keys():
        if key == "owner_id":
            ownerId: str = str(guildData.get("owner_id", ""))
            if ownerId.isdigit():
                ownerId = int(ownerId)
            else:
                ownerId = 0
            owner: discord.Member | None = getMemberGuild(guild, ownerId)
            if owner is not None:
                try:
                    await guild.edit(reason=reason, owner=owner)
                    success = True
                except Exception:
                    continue
        elif key == "afk_channel_id":
            afk_channel: str = str(guildData.get("afk_channel_id", ""))
            afk_channel_obj = getVoiceChannelGuild(guild, int(afk_channel) if afk_channel.isdigit() else 0)
            if afk_channel_obj != guild.afk_channel:
                try:
                    await guild.edit(reason=reason, afk_channel=afk_channel_obj)
                    success = True
                except Exception:
                    continue
        elif key == "system_channel_id":
            system_channel: str = str(guildData.get("system_channel_id", ""))
            system_channel_obj = getVoiceChannelGuild(guild,
                                                      int(system_channel) if system_channel.isdigit() else 0)
            if system_channel_obj != guild.system_channel:
                try:
                    await guild.edit(reason=reason, afk_channel=system_channel_obj)
                    success = True
                except Exception:
                    continue
        elif key == "afk_timeout":
            afk_timeout: str = str(guildData.get("afk_timeout", ""))
            if afk_timeout.isdigit() and int(afk_timeout) != guild.afk_timeout:
                try:
                    await guild.edit(reason=reason, afk_timeout=int(afk_timeout))
                    success = True
                except Exception:
                    continue
        elif key == "rules_channel_id":
            rules_channel: str = str(guildData.get("rules_channel_id", ""))
            rules_channel_obj = getTextChannel(guild, int(rules_channel) if rules_channel.isdigit() else 0)
            if rules_channel_obj != guild.rules_channel:
                try:
                    await guild.edit(reason=reason, rules_channel=rules_channel_obj)
                    success = True
                except Exception:
                    continue
        elif key == "public_updates_channel_id":
            public_updates_channel: str = str(guildData.get("public_updates_channel_id", ""))
            public_updates_channel_obj = getTextChannel(guild,
                                                        int(public_updates_channel)
                                                        if public_updates_channel.isdigit() else 0)
            if public_updates_channel_obj != guild.rules_channel:
                try:
                    await guild.edit(reason=reason, public_updates_channel=public_updates_channel_obj)
                    success = True
                except Exception:
                    continue
        elif key == "widget_channel_id":
            widget_channel: str = str(guildData.get("widget_channel_id", ""))
            widget_channel_obj = getTextChannel(guild, int(widget_channel) if widget_channel.isdigit() else 0)
            if widget_channel_obj != guild.widget_channel:
                try:
                    await guild.edit(reason=reason, widget_channel=widget_channel_obj)
                    success = True
                except Exception:
                    continue
        elif key == "safety_alerts_channel_id":
            safety_alerts_channel: str = str(guildData.get("safety_alerts_channel_id", ""))
            try:
                if safety_alerts_channel.isdigit() and int(
                        safety_alerts_channel) != guild.safety_alerts_channel.id:
                    await guild.edit(reason=reason,
                                     safety_alerts_channel=getTextChannel(guild, int(safety_alerts_channel)))
                success = True
            except Exception:
                continue
        elif key == "description":
            description = guildData.get("description")
            if guild.description != description:
                try:
                    await guild.edit(reason=reason, description=description)
                    success = True
                except Exception:
                    continue
        elif key == "icon":
            icon = guildData.get("icon")
            if icon is bytes and guild.icon != icon:
                try:
                    await guild.edit(reason=reason, icon=icon)
                    success = True
                except Exception:
                    continue
        elif key == "name":
            name: str = str(guildData.get("name", ""))
            if name is not None and guild.name != name and len(name.replace(" ", "")) > 0:
                try:
                    await guild.edit(reason=reason, name=name)
                    success = True
                except Exception:
                    continue
        elif key == "banner":
            banner = guildData.get("banner")
            if guild.banner != banner:
                try:
                    await guild.edit(reason=reason, banner=banner)
                    success = True
                except Exception:
                    continue
        elif key == "splash":
            splash = guildData.get("splash")
            if splash is bytes and rq.get(guild.splash.url).content != splash:
                try:
                    await guild.edit(reason=reason, splash=splash)
                    success = True
                except Exception:
                    continue
        elif key == "discovery_splash":
            discovery_splash = guildData.get("discovery_splash")
            if discovery_splash is bytes and rq.get(guild.discovery_splash.url).content != discovery_splash:
                try:
                    await guild.edit(reason=reason, discovery_splash=discovery_splash)
                    success = True
                except Exception:
                    continue
        elif key == "default_notifications":
            default_notifications: discord.NotificationLevel | None = getattr(discord.NotificationLevel,
                                                                              str(guildData.get(
                                                                                  "default_notifications")).lower(),
                                                                              None)
            if default_notifications is not None and guild.default_notifications != default_notifications:
                try:
                    await guild.edit(reason=reason, default_notifications=default_notifications)
                    success = True
                except Exception:
                    continue
        elif key == "verification_level":
            verification_level: discord.VerificationLevel | None = getattr(discord.VerificationLevel,
                                                                           str(guildData.get(
                                                                               "verification_level")).lower(),
                                                                           None)
            if verification_level is not None and guild.verification_level != verification_level:
                try:
                    await guild.edit(reason=reason, verification_level=verification_level)
                    success = True
                except Exception:
                    continue
        elif key == "content_filter":
            explicit_content_filter: discord.ContentFilter | None = getattr(discord.ContentFilter,
                                                                            str(guildData.get(
                                                                                "content_filter")).lower(),
                                                                            None)
            if explicit_content_filter is not None and guild.explicit_content_filter != explicit_content_filter:
                try:
                    await guild.edit(reason=reason, explicit_content_filter=explicit_content_filter)
                    success = True
                except Exception:
                    continue
        elif key == "preferred_locale":
            preferred_locale: discord.Locale | None = getattr(discord.Locale,
                                                              str(guildData.get(
                                                                  "preferred_locale")).lower(),
                                                              None)
            if preferred_locale is not None and preferred_locale != guild.preferred_locale:
                try:
                    await guild.edit(reason=reason, preferred_locale=preferred_locale)
                    success = True
                except Exception:
                    continue
        elif key == "mfa_level":
            mfa_level: discord.MFALevel | None = getattr(discord.MFALevel,
                                                         str(guildData.get("mfa_level")).lower(),
                                                         None)
            if mfa_level is not None and mfa_level != guild.mfa_level:
                try:
                    await guild.edit(reason=reason, mfa_level=mfa_level)
                    success = True
                except Exception:
                    continue
        elif key == "vanity_code":
            vanity_code: str | None = guildData.get("vanity_code", None)
            if vanity_code is not None:
                try:
                    await guild.edit(reason=reason, vanity_code=vanity_code)
                    success = True
                except Exception:
                    continue
        elif key == "discoverable":
            try:
                await guild.edit(reason=reason, discoverable=bool(guildData.get("discoverable")))
                success = True
            except Exception:
                continue
        elif key == "invites_disabled":
            try:
                await guild.edit(reason=reason, invites_disabled=bool(guildData.get("invites_disabled")))
                success = True
            except Exception:
                continue
        elif key == "raid_alerts_disabled":
            try:
                await guild.edit(reason=reason,
                                 raid_alerts_disabled=bool(guildData.get("raid_alerts_disabled")))
                success = True
            except Exception:
                continue
        elif key == "community":
            try:
                await guild.edit(reason=reason, community=bool(guildData.get("community")))
                success = True
            except Exception:
                continue

    return success


def getTextChannel(guild: discord.Guild, channelId: int) -> discord.TextChannel | None:
    if channelId == 0:
        return None
    channel = guild.get_channel(channelId)
    return channel if type(channel) == discord.TextChannel else None


def getUsers(userData: dict, guild: discord.Guild) -> List[discord.User]:
    userIds = userData.get("user_id")
    userNames = userData.get("user_name")
    if isinstance(userIds, int):
        userIds = [userIds]
    elif not isinstance(userIds, list):
        userIds = []

    if isinstance(userNames, str):
        userNames = [userNames]
    elif not isinstance(userNames, list):
        userNames = []

    users: list = []
    for ids in userIds:
        member: discord.Member | None = guild.get_member(ids)
        if member is not None:
            users.append(member)
    for name in userNames:
        member: discord.Member | None = discord.utils.get(guild.members, name=name)
        if member is not None:
            users.append(member)
    return users


async def createCategory(categoryData: dict, guild: discord.Guild) -> discord.CategoryChannel | None:
    try:
        position = categoryData.get("position")
        if not isinstance(position, int):
            position = 1
        permissions = categoryData.get("permissions")
        if isinstance(permissions, dict):
            category: discord.CategoryChannel = await guild.create_category(
                name=str(categoryData.get("name", "CategoryName")), position=position,
                reason=str(categoryData.get("reason", "")), overwrites=getPermissionsMapping(permissions, guild))
        else:
            category: discord.CategoryChannel = await guild.create_category(
                name=str(categoryData.get("name", "CategoryName")), position=position,
                reason=str(categoryData.get("reason", "")))
        return category
    except Exception:
        return None


def getCategoryData(category: discord.CategoryChannel) -> dict:
    data: dict = dict()
    data["name"] = category.name
    data["id"] = category.id
    data["position"] = category.position
    data["created_at"] = category.created_at
    data["type"] = category.type.name
    data["jump_url"] = category.jump_url
    data["is_nsfw"] = category.is_nsfw()
    data["category_id"] = category.category_id
    #data["permissions"] = category.overwrites
    data["permissions"] = getPermissionsDataFromMapping(category.overwrites)
    print(data["permissions"])
    return data


async def deleteCategory(category: discord.CategoryChannel, reason: str = "") -> bool:
    try:
        await category.delete(reason=reason)
        return True
    except Exception:
        return False


def getPermissionsMapping(permissions: dict, guild: discord.Guild) -> Mapping[Union[Role, discord.Member], discord.PermissionOverwrite]:

    overwrites = {}
    users: list = permissions.get("users")
    roles: list = permissions.get("roles")
    if not isinstance(users, list):
        users = []
    if not isinstance(roles, list):
        roles = []
    for role in roles:
        if not isinstance(role, dict):
            continue
        for r in getRoles(role, guild):
            perms = role.get("permissions")
            if not isinstance(perms, dict):
                continue
            overwrites[r] = discord.PermissionOverwrite(**perms)
    for user in users:
        if not isinstance(user, dict):
            continue
        for u in getUsers(user, guild):
            perms = user.get("permissions")
            if not isinstance(perms, dict):
                continue
            overwrites[u] = discord.PermissionOverwrite(**perms)

    return overwrites


def getPermissionsDataFromMapping(mapping: Mapping[Union[Role, discord.Member], discord.PermissionOverwrite]) -> dict:
    data: dict = dict()
    data["roles"] = []
    data["users"] = []
    for obj, permoverride in mapping.items():
        if isinstance(obj, discord.Role):
            roleData: dict = dict()
            roleData["role_name"] = obj.name
            roleData["role_id"] = obj.id
            roleData["permissions"] = dict()
            for name in permoverride.VALID_NAMES:
                res = getattr(permoverride, name, None)
                if res is None:
                    continue
                roleData["permissions"][name] = res
            data["roles"].append(roleData)
        elif isinstance(obj, discord.User) or isinstance(obj, discord.Member):
            userData: dict = dict()
            userData["user_name"] = obj.name
            userData["user_id"] = obj.id
            userData["permissions"] = dict()
            for name in permoverride.VALID_NAMES:
                res = getattr(permoverride, name, None)
                if res is None:
                    continue
                userData["permissions"][name] = res
            data["users"].append(userData)
    return data


async def editCategory(categoryData: dict, guild: discord.Guild) -> bool:
    pass


def getCategories(categoryData: dict, guild: discord.Guild) -> List[discord.CategoryChannel]:
    categoryIds = categoryData.get("category_id")
    categoryNames = categoryData.get("category_name")
    if isinstance(categoryIds, int):
        categoryIds = [categoryIds]
    elif not isinstance(categoryIds, list):
        categoryIds = []

    if isinstance(categoryNames, str):
        categoryNames = [categoryNames]
    elif not isinstance(categoryNames, list):
        categoryNames = []

    categories: list = []
    for ids in categoryIds:
        for cat in guild.categories:
            if cat.id == ids:
                categories.append(cat)
    for name in categoryNames:
        for cat in guild.categories:
            if cat.name == name:
                categories.append(cat)
    return categories
