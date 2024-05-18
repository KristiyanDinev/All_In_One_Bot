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


