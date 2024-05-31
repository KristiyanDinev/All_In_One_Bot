from __future__ import annotations

from typing import List, Mapping, Union, Any
import requests as rq
import asyncio
import discord
from discord.ext import commands
from discord import Role

from cogs.ext.config_manager import ConfigManager
import cogs.ext.utils.messages as messages

configManager = ConfigManager("configs/config", "configs/messages",
                              "configs/warnings",
                              "configs/commands")


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
    return channel if isinstance(channel, discord.VoiceChannel) else None


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


async def isUserRestricted(bot: commands.Bot, commandName: str, executionPath: str,
                           interaction: discord.Interaction | None = None,
                           ctx: discord.ext.commands.context.Context | None = None) -> str:
    res = configManager.getCommandRestrictions(commandName)
    reason = ""

    for option, data in res.items():
        if not isinstance(data, dict):
            res = await messages.handleError(bot, commandName, executionPath,
                                             "Expected map in command restrictions, but got type " + str(type(data)),
                                             placeholders=dict(),
                                             interaction=interaction, ctx=ctx)
            if res:
                continue
            else:
                reason += "Expected map in command restrictions, but got type " + str(type(data))
                break
        dataReason = data.get("reason", "")
        userRoleId: list = getRoleIdFromRoles(interaction.user.roles)
        status = data.get("status", [])
        if option == "all":
            if bool(data.get("status", True)):
                return reason
            else:
                reason += dataReason
        elif (option == "users_id" and isinstance(status, list) and
              (interaction.user.id if interaction is not None else ctx.author.id) not in status):
            reason += dataReason
        elif option == "any_roles_id" and isinstance(status, list) and anyRolesContains(status, userRoleId):
            reason += dataReason
        elif option == "all_roles_id" and isinstance(status, list) and allRolesContains(status, userRoleId):
            reason += dataReason
        elif (option == "channels_id" and isinstance(status, list) and
              (interaction.channel.id if interaction is not None else ctx.channel.id) not in status):
            reason += dataReason

    return reason


def separateThread(loop, func, *args):
    asyncio.run_coroutine_threadsafe(func(*args), loop)


async def giveRoleToUser(user: discord.User, role: discord.Role, reason: str = ""):
    await user.add_roles(role, reason=reason)


async def removeRoleToUser(member: discord.Member, role: discord.Role, reason: str = ""):
    await member.remove_roles(role, reason=reason)


async def createRoleWithDisplayIcon(roleData: dict, guild: discord.Guild) -> discord.Role | None:
    try:
        role: discord.Role = await guild.create_role(reason=roleData.get("reason", ""),
                                                     name=roleData.get("name", "No Name Given"),
                                                     display_icon=roleData.get("display_icon"),
                                                     color=getColour(str(roleData.get("color", ""))),
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
                                                     color=getColour(str(roleData.get("color", ""))),
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


async def deleteRoleFromData(roleData: dict, guild: discord.Guild) -> List[discord.Role] | None:
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


async def deleteRole(role: discord.Role, reason: str):
    await role.delete(reason=reason)

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


async def banUser(member: discord.Member, reason: str = ""):
    await member.ban(reason=reason)


async def unbanUser(member: discord.Member, reason: str = ""):
    await member.unban(reason=reason)


async def kickUser(member: discord.Member, reason: str = ""):
    await member.kick(reason=reason)


async def addRole(member: discord.Member, role: discord.Role, reason: str = ""):
    await member.add_roles(role, reason=reason)


async def removeRole(member: discord.Member, role: discord.Role, reason: str = ""):
    await member.remove_roles(role, reason=reason)


async def timeoutUser(member: discord.Member, datetime_zone, reason: str = ""):
    await member.timeout(datetime_zone, reason=reason)


async def removeUserTimeout(member: discord.Member, reason: str = ""):
    await member.edit(timed_out_until=None, reason=reason)


async def userDeafen(member: discord.Member, status: bool, reason: str = ""):
    await member.edit(deafen=status, reason=reason)


async def userMute(member: discord.Member, status: bool, reason: str = ""):
    await member.edit(mute=status, reason=reason)


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


async def editRole(roleData: dict, role: discord.Role) -> dict:
    position: str | None = str(roleData.get("position", None))
    reason: str = str(roleData.get("reason", ""))
    if not isinstance(position, int):
        position: int = role.position

    name: str = str(roleData.get("new_name", role.name))
    colour: discord.Colour = getColour(str(roleData.get("color", role.colour)))
    hoist: bool = bool(roleData.get("hoist", role.hoist))
    mentionable: bool = bool(bool(roleData.get("mentionable", role.mentionable)))
    permissions: discord.Permissions = getDiscordPermission(dict(roleData.get("permissions", {})))

    roleStatus: dict = dict()
    if "ROLE_ICONS" in role.guild.features:
        try:
            await role.edit(name=name, reason=reason, colour=colour, hoist=hoist, mentionable=mentionable,
                            position=position, permissions=permissions, display_icon=roleData.get("display_icon", None))
        except Exception as e:
            roleStatus["role_edit_error"] = e
        finally:
            roleStatus["role_edit"] = True
    else:
        try:
            await role.edit(name=name, reason=str(roleData.get("reason", "")), colour=colour, hoist=hoist,
                            mentionable=mentionable, position=position, permissions=permissions)
        except Exception as e:
            roleStatus["role_edit_error"] = e
        finally:
            roleStatus["role_edit"] = True

    if "users" in roleData.keys():
        users: list = roleData.get("users", [])
        if not isinstance(users, list):
            return roleStatus
        roleStatus["role_remove_user_error"] = []
        roleStatus["role_remove_user_success"] = []

        roleStatus["role_add_user_error"] = []
        roleStatus["role_add_user_success"] = []
        for member in role.members:
            if member.id in users:
                continue
            try:
                await removeRole(member, role, reason=reason)
            except Exception as e:
                roleStatus["role_remove_user_error"].append({"error": e, "message":
                    f"Couldn't remove the role {role.name} : {role.id} from {member.name} : {member.id}"})
            finally:
                roleStatus["role_remove_user_success"].append({"message":
                                     f"Removed the role {role.name} : {role.id} from {member.name} : {member.id}"})

        for userId in users:
            member: discord.Member | None = getMemberGuild(role.guild, userId)
            if member is None or memberHasRole(member, role):
                roleStatus["role_add_user_error"].append({"message":
                                    f"there is no member with ID {userId} or member already has this role"})
                continue
            try:
                await addRole(member, role, reason=reason)
            except Exception as e:
                roleStatus["role_add_user_error"].append({"error": e, "message":
                         f"Couldn't add role {role.name} : {role.id} to member {member.name} : {member.id}"})
            finally:
                roleStatus["role_add_user_success"].append({"message": True})


def getColour(color: str) -> discord.Colour:
    try:
        return discord.Colour.random() if color == "random" or len(color) == 0 else discord.Colour.from_str(color)
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


def getUsers(userData: dict, guild: discord.Guild) -> List[discord.Member]:
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
        if not isinstance(permissions, dict):
            permissions = dict()
        category: discord.CategoryChannel = await guild.create_category(
            name=str(categoryData.get("name", "CategoryName")), position=position,
            reason=str(categoryData.get("reason", "")), overwrites=getPermissionsMapping(permissions, guild))
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
    data["nsfw"] = category.is_nsfw()
    data["category_id"] = category.category_id
    data["permissions"] = getPermissionsDataFromMapping(category.overwrites)
    return data


async def deleteCategory(category: discord.CategoryChannel, reason: str = "") -> bool:
    try:
        await category.delete(reason=reason)
        return True
    except Exception:
        return False


def getPermissionsMapping(permissions: dict, guild: discord.Guild) -> Mapping[
    Union[Role, discord.Member], discord.PermissionOverwrite]:
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


async def editCategory(category: discord.CategoryChannel, categoryData: dict) -> bool:
    try:
        position: int = categoryData.get("position")
        if not isinstance(position, int):
            position = category.position
        permissions = categoryData.get("permissions")
        if isinstance(permissions, dict):
            await category.edit(reason=str(categoryData.get("reason", "")), name=str(categoryData.get("new_name", "")),
                                position=position, nsfw=bool(categoryData.get("nsfw", False)),
                                overwrites=getPermissionsMapping(permissions, category.guild))
        else:
            await category.edit(reason=str(categoryData.get("reason", "")), name=str(categoryData.get("new_name", "")),
                                position=position, nsfw=bool(categoryData.get("nsfw", False)))
        return True
    except Exception:
        return False


def getCategories(categoryData: dict, guild: discord.Guild) -> list[None] | list:
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
    if len(categories) == 0:
        return [None]
    return categories


def getChannels(channelData: dict, guild: discord.Guild) -> list:
    channelIds = channelData.get("channel_id")
    channelNames = channelData.get("channel_name")
    if isinstance(channelIds, int):
        channelIds = [channelIds]
    elif not isinstance(channelIds, list):
        channelIds = []

    if isinstance(channelNames, str):
        channelNames = [channelNames]
    elif not isinstance(channelNames, list):
        channelNames = []

    channels: list = []
    for ids in channelIds:
        for cha in guild.channels:
            if cha.id == ids:
                channels.append(cha)
    for name in channelNames:
        for cha in guild.channels:
            if cha.name == name:
                channels.append(cha)

    category_name = channelData.get("category_name")
    if isinstance(category_name, str):
        category_name = [category_name]
    if not isinstance(category_name, list):
        category_name = []

    category_id = channelData.get("category_id")
    if isinstance(category_id, int):
        category_id = [category_id]
    if not isinstance(category_id, list):
        category_id = []

    for i in range(len(channels)):
        channel = channels[i]
        if not (channel.category is not None and (
                channel.category.id in category_id or channel.category.name in category_name)):
            channels.pop(i)
    return channels


async def createChannel(channelData: dict, guild: discord.Guild) -> list:
    channel_type: str = str(channelData.get("type")).lower()
    permissions = channelData.get("permissions")
    if not isinstance(permissions, dict):
        permissions = dict()

    position: int = channelData.get("position")
    if not isinstance(position, int):
        position = 1

    bitrate: int | None = channelData.get("bitrate")
    if not isinstance(bitrate, int):
        bitrate = 64

    user_limit: int | None = channelData.get("user_limit")
    if not isinstance(user_limit, int):
        user_limit = None

    video_quality_mode: discord.VideoQualityMode | None = getattr(discord.VideoQualityMode,
                                                                  str(channelData.get("video_quality_mode", "")),
                                                                  None)

    overwrite = getPermissionsMapping(permissions, guild)
    createdChannels: list = []
    categories = [None]
    if "category_name" in channelData.keys() or "category_id" in channelData.keys():
        categories = getCategories(channelData, guild)
    for category in categories:
        if channel_type == "voice":
            channel = await guild.create_voice_channel(name=str(channelData.get("name", "ChannelName")),
                                                       reason=str(channelData.get("reason")), category=category,
                                                       position=position,
                                                       rtc_region=channelData.get("rtc_region", None),
                                                       overwrites=overwrite)
            if bitrate is not None:
                await channel.edit(bitrate=bitrate)
            if user_limit is not None:
                await channel.edit(user_limit=user_limit)
            if video_quality_mode is not None:
                await channel.edit(video_quality_mode=video_quality_mode)
            createdChannels.append(channel)
        elif channel_type == "stage":
            channel = await guild.create_stage_channel(name=str(channelData.get("name", "ChannelName")),
                                                       reason=str(channelData.get("reason")), category=category,
                                                       position=position,
                                                       rtc_region=channelData.get("rtc_region", None),
                                                       overwrites=overwrite, bitrate=bitrate)
            if user_limit is not None:
                await channel.edit(user_limit=user_limit)
            if video_quality_mode is not None:
                await channel.edit(video_quality_mode=video_quality_mode)
            createdChannels.append(channel)
        elif channel_type == "form":
            channel = await guild.create_forum(name=str(channelData.get("name", "ChannelName")),
                                               reason=str(channelData.get("reason")), category=category,
                                               position=position, nsfw=bool(channelData.get("nsfw", False)),
                                               overwrites=overwrite)
            if "topic" in channelData.keys():
                await channel.edit(topic=str(channelData.get("topic")))

            slowmode_delay = channelData.get("slowmode_delay")
            if isinstance(slowmode_delay, int):
                await channel.edit(slowmode_delay=slowmode_delay)

            default_auto_archive_duration = channelData.get("default_auto_archive_duration")
            if isinstance(default_auto_archive_duration, int):
                await channel.edit(default_auto_archive_duration=default_auto_archive_duration)

            default_thread_slowmode_delay = channelData.get("default_thread_slowmode_delay")
            if isinstance(default_thread_slowmode_delay, int):
                await channel.edit(default_thread_slowmode_delay=default_thread_slowmode_delay)

            default_sort_order = getattr(discord.ForumOrderType, str(channelData.get("default_sort_order", "")),
                                         None)
            if default_sort_order is not None:
                await channel.edit(default_sort_order=default_sort_order)

            default_reaction_emoji = channelData.get("default_reaction_emoji", None)
            if default_reaction_emoji is not None:
                await channel.edit(default_reaction_emoji=str(default_reaction_emoji))

            default_layout = getattr(discord.ForumLayoutType, str(channelData.get("default_layout", "")),
                                     None)
            if default_layout is not None:
                await channel.edit(default_layout=default_layout)

            available_tags = channelData.get("available_tags")
            if isinstance(available_tags, list):
                try:
                    await channel.edit(available_tags=available_tags)
                except Exception:
                    pass

            createdChannels.append(channel)
        else:
            channel = await guild.create_text_channel(name=str(channelData.get("name", "ChannelName")),
                                                      reason=str(channelData.get("reason")), category=category,
                                                      position=position,
                                                      overwrites=overwrite, news=bool(channelData.get("news", False)),
                                                      nsfw=bool(channelData.get("nsfw", False)))
            if "topic" in channelData.keys():
                await channel.edit(topic=str(channelData.get("topic")))

            slowmode_delay = channelData.get("slowmode_delay")
            if isinstance(slowmode_delay, int):
                await channel.edit(slowmode_delay=slowmode_delay)

            default_auto_archive_duration = channelData.get("default_auto_archive_duration")
            if isinstance(default_auto_archive_duration, int):
                await channel.edit(default_auto_archive_duration=default_auto_archive_duration)

            default_thread_slowmode_delay = channelData.get("default_thread_slowmode_delay")
            if isinstance(default_thread_slowmode_delay, int):
                await channel.edit(default_thread_slowmode_delay=default_thread_slowmode_delay)

            createdChannels.append(channel)
    return createdChannels


async def deleteChannel(
        channel: Union[discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.ForumChannel],
        reason: str = "") -> bool:
    try:
        await channel.delete(reason=reason)
        return True
    except Exception:
        return False


def getChannelData(
        channel: Union[discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.ForumChannel]) -> dict:
    data: dict = dict()
    data["name"] = channel.name
    data["permissions"] = getPermissionsDataFromMapping(channel.overwrites)
    data["position"] = channel.position
    if channel.category is not None:
        data["category_id"] = channel.category.id
        data["category_name"] = channel.category.name
    if isinstance(channel, discord.TextChannel):
        data["topic"] = channel.topic
        data["slowmode_delay"] = channel.slowmode_delay
        data["default_thread_slowmode_delay"] = channel.default_thread_slowmode_delay
        data["default_auto_archive_duration"] = channel.default_auto_archive_duration
    elif isinstance(channel, discord.VoiceChannel):
        data["bitrate"] = channel.bitrate
        data["user_limit"] = channel.user_limit
        data["video_quality_mode"] = channel.video_quality_mode
        data["rtc_region"] = channel.rtc_region
    elif isinstance(channel, discord.StageChannel):
        data["user_limit"] = channel.user_limit
        data["video_quality_mode"] = channel.video_quality_mode
        data["rtc_region"] = channel.rtc_region
    elif isinstance(channel, discord.ForumChannel):
        data["nsfw"] = channel.nsfw
        data["topic"] = channel.topic
        data["slowmode_delay"] = channel.slowmode_delay
        data["default_auto_archive_duration"] = channel.default_auto_archive_duration
        data["default_thread_slowmode_delay"] = channel.default_thread_slowmode_delay
        data["default_sort_order"] = channel.default_sort_order
        data["default_reaction_emoji"] = channel.default_reaction_emoji
        data["default_layout"] = channel.default_layout
        data["available_tags"] = channel.available_tags
    return data


async def editChannel(channelData: dict,
                      channel: Union[
                          discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.ForumChannel]) -> bool:
    try:
        channelDataCopy = channelData.copy()
        channelDataCopy["category_name"] = channelDataCopy.pop("new_category_name")
        channelDataCopy["category_id"] = channelDataCopy.pop("new_category_id")
        permissions = channelDataCopy.get("permissions")
        if not isinstance(permissions, dict):
            permissions = dict()
        overwrites = getPermissionsMapping(permissions, channel.guild)
        video_quality_mode: discord.VideoQualityMode | None = getattr(discord.VideoQualityMode,
                                                                      str(channelDataCopy.get("video_quality_mode",
                                                                                              "")),
                                                                      None)
        for new_category in getCategories(channelDataCopy, channel.guild):
            position: int = channelDataCopy.get("position")
            if isinstance(position, int):
                await channel.edit(position=position)

            slowmode_delay: int = channelDataCopy.get("slowmode_delay")
            if isinstance(slowmode_delay, int):
                await channel.edit(slowmode_delay=slowmode_delay)

            if isinstance(channel, discord.TextChannel):
                await channel.edit(name=str(channelDataCopy.get("new_name", "NewChannelName")),
                                   reason=str(channelDataCopy.get("reason", "")),
                                   nsfw=bool(channelDataCopy.get("nsfw", False)),
                                   sync_permissions=bool(channelDataCopy.get("sync_permissions", False)),
                                   category=new_category,
                                   overwrites=overwrites)
                if "topic" in channelDataCopy.keys():
                    await channel.edit(topic=str(channelDataCopy.get("topic")))

                default_auto_archive_duration: int = channelDataCopy.get("default_auto_archive_duration")
                if isinstance(default_auto_archive_duration, int):
                    await channel.edit(default_auto_archive_duration=default_auto_archive_duration)

                default_thread_slowmode_delay: int = channelDataCopy.get("default_thread_slowmode_delay")
                if isinstance(default_thread_slowmode_delay, int):
                    await channel.edit(default_thread_slowmode_delay=default_thread_slowmode_delay)
            elif isinstance(channel, discord.VoiceChannel):
                await channel.edit(name=str(channelDataCopy.get("new_name", "NewChannelName")),
                                   reason=str(channelDataCopy.get("reason", "")),
                                   nsfw=bool(channelDataCopy.get("nsfw", False)),
                                   sync_permissions=bool(channelDataCopy.get("sync_permissions", False)),
                                   category=new_category, overwrites=overwrites,
                                   rtc_region=None if not isinstance(channelDataCopy.get("rtc_region", None), str)
                                   else channelDataCopy.get("rtc_region"))

                user_limit: int = channelDataCopy.get("user_limit")
                if isinstance(user_limit, int):
                    await channel.edit(user_limit=user_limit)
                bitrate: int = channelDataCopy.get("bitrate")
                if isinstance(bitrate, int):
                    await channel.edit(bitrate=bitrate)

                if video_quality_mode is not None:
                    await channel.edit(video_quality_mode=video_quality_mode)
            elif isinstance(channel, discord.StageChannel):
                await channel.edit(name=str(channelDataCopy.get("new_name", "NewChannelName")),
                                   reason=str(channelDataCopy.get("reason", "")),
                                   nsfw=bool(channelDataCopy.get("nsfw", False)),
                                   sync_permissions=bool(channelDataCopy.get("sync_permissions", False)),
                                   category=new_category, overwrites=overwrites,
                                   rtc_region=None if not isinstance(channelDataCopy.get("rtc_region", None), str)
                                   else channelDataCopy.get("rtc_region"))

                user_limit: int = channelDataCopy.get("user_limit")
                if isinstance(user_limit, int):
                    await channel.edit(user_limit=user_limit)

                if video_quality_mode is not None:
                    await channel.edit(video_quality_mode=video_quality_mode)
            elif isinstance(channel, discord.ForumChannel):
                await channel.edit(name=str(channelDataCopy.get("new_name", "NewChannelName")),
                                   reason=str(channelDataCopy.get("reason", "")),
                                   nsfw=bool(channelDataCopy.get("nsfw", False)),
                                   sync_permissions=bool(channelDataCopy.get("sync_permissions", False)),
                                   category=new_category,
                                   overwrites=overwrites)

                if "topic" in channelDataCopy.keys():
                    await channel.edit(topic=str(channelDataCopy.get("topic")))

                default_auto_archive_duration: int = channelDataCopy.get("default_auto_archive_duration")
                if isinstance(default_auto_archive_duration, int):
                    await channel.edit(default_auto_archive_duration=default_auto_archive_duration)

                available_tags = channelData.get("available_tags")
                if isinstance(available_tags, list):
                    try:
                        await channel.edit(available_tags=available_tags)
                    except Exception:
                        pass

        return True
    except Exception:
        return False
