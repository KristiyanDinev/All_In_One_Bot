from __future__ import annotations

from typing import List

import discord
import os, sys, json
from discord.ext import commands
from discord import app_commands, Member, Role
from cogs.ext.config_manager import ConfigManager

configManager = ConfigManager("configs/config", "configs/messages",
                              "configs/warnings", "configs/commands")


async def setup(bot: commands.Bot):
    pass


async def sendResponse(interaction: discord.Interaction, message: str, embed: discord.Embed):
    if len(message.replace(" ", "")) == 0:
        message = None

    if message is None and embed is None:
        return

    eph = configManager.getEphPlaceholder()

    try:
        await interaction.response.send_message(message, embed=embed,
                                                ephemeral=True
                                                if configManager.isActivePlaceholder(eph) and
                                                   (message is not None and eph is not None and eph in message)
                                                else False)
    except Exception as e:
        print(e)
        try:
            await interaction.channel.send(message, embed=embed)
        except Exception as e:
            print(e)
            pass


async def sendResponseCtx(ctx: discord.ext.commands.context.Context, message: str, embed: discord.Embed):
    if len(message.replace(" ", "")) == 0:
        message = None

    eph = configManager.getEphPlaceholder()

    try:
        await ctx.reply(message, embed=embed,
                        ephemeral=True
                        if configManager.isActivePlaceholder(eph) and
                           (message is not None and eph is not None and eph in message)
                        else False)
    except Exception as e:
        print(e)
        try:
            await ctx.send(message, embed=embed)
        except Exception as e:
            print(e)
            pass


def buildMessages(command_name: str, error_name: str = "", placeholders: dict = dict()):
    if len(error_name.replace(" ", "")) > 0:
        error_embed = buildEmbed(command_name, error_name, placeholders)
        message: str = configManager.getCommandMessages(command_name, error_name)
        if len(message.replace(" ", "")) != 0:
            for placeholder, v in placeholders.items():
                if configManager.isActivePlaceholder(placeholder):
                    message = message.replace(placeholder, v)
        return message, error_embed

    for msg in configManager.getCommandData(command_name).get("message_names", []):
        message: str = configManager.getCommandMessages(command_name, msg)
        embed = None
        if configManager.getCommandEmbeds(command_name, msg) is not None:
            embed = buildEmbed(command_name, msg, placeholders)

        if len(message.replace(" ", "")) != 0:
            for placeholder, v in placeholders.items():
                if configManager.isActivePlaceholder(placeholder):
                    message = message.replace(placeholder, v)
        return message, embed
    return "", None


async def handleMessage(interaction: discord.Interaction, command_name: str, error_name: str = "",
                        placeholders: dict = dict()):
    msg, emb = buildMessages(command_name, error_name, placeholders)
    await sendResponse(interaction, msg, emb)


async def handleMessageCtx(ctx: discord.ext.commands.context.Context, command_name: str, error_name: str = "",
                           placeholders: dict = dict()):
    msg, emb = buildMessages(command_name, error_name, placeholders)
    await sendResponseCtx(ctx, msg, emb)


def buildEmbed(command: str, message_key: str, placeholders: dict):
    try:
        data: dict = configManager.getCommandEmbeds(command, message_key)

        title: str = data.get(configManager.getEmbedTitle())
        author_name: str = data.get(configManager.getEmbedAuthorName())
        author_url: str = data.get(configManager.getEmbedAuthorUrl())
        author_icon_url: str = data.get(configManager.getEmbedAuthorIconUrl())
        footer_text: str = data.get(configManager.getEmbedFooter())
        footer_icon_url: str = data.get(configManager.getEmbedFooterIconUrl())
        image_url: str = data.get(configManager.getEmbedImageUrl())
        desc: str = data.get(configManager.getEmbedDescription())
        colour: str = data.get(configManager.getEmbedColor())

        for placeholder, v in placeholders.items():
            if configManager.isActivePlaceholder(placeholder):
                title = title.replace(placeholder, v)
                author_name = author_name.replace(placeholder, v)
                author_url = author_url.replace(placeholder, v)
                author_icon_url = author_icon_url.replace(placeholder, v)
                footer_text = footer_text.replace(placeholder, v)
                footer_icon_url = footer_icon_url.replace(placeholder, v)
                image_url = image_url.replace(placeholder, v)
                desc = desc.replace(placeholder, v)

        embed = discord.Embed(title=title,
                              colour=discord.Colour.random() if colour == "random" else discord.Colour.from_str(colour),
                              description=desc)

        embed.set_author(name=author_name,
                         url=author_url,
                         icon_url=author_icon_url)

        embed.set_footer(text=footer_text,
                         icon_url=footer_icon_url)

        embed.set_image(url=image_url)

        for k, v in data.get(configManager.getEmbedFields()).items():
            embed.add_field(name=k, value=v)

        return embed

    except Exception as e:
        return None


def getMember(interaction: discord.Interaction, member_id: int) -> Member | None:
    if member_id == 0:
        return None
    member = interaction.guild.get_member(member_id)
    return member


async def handleInvalidMember(interaction: discord.Interaction, command: str):
    await handleMessage(interaction, command,
                        error_name=configManager.getInvalidMemberKey(),
                        placeholders={configManager.getUsernamePlaceholder(): configManager.getInvalidMember()})


async def handleInvalidRole(interaction: discord.Interaction, command: str):
    await handleMessage(interaction, command,
                        error_name=configManager.getInvalidRoleKey(),
                        placeholders={configManager.getRoleNamePlaceholder(): configManager.getInvalidRole()})


async def handleInvalidArg(interaction: discord.Interaction, command: str):
    await handleMessage(interaction, command,
                        error_name=configManager.getInvalidArgsKey(),
                        placeholders={configManager.getErrorPlaceholder(): configManager.getInvalidArg()})


async def handleErrors(interaction: discord.Interaction, command: str, error):
    await handleMessage(interaction, command,
                        error_name=configManager.getUnknownErrorKey(),
                        placeholders={configManager.getErrorPlaceholder(): error})


async def handleInvalidChannels(interaction: discord.Interaction, command: str):
    await handleMessage(interaction, command,
                        error_name=configManager.getInvalidChannelKey(),
                        placeholders={configManager.getChannelNamePlaceholder(): configManager.getInvalidChannel()})


def get_role_id_from_mention(role_mention: str) -> int:
    try:
        return int(role_mention.replace("<@&", "")[:-1])
    except Exception:
        return 0


def get_member_id_from_mention(member_mention: str) -> int:
    try:
        return int(member_mention.replace("<@", "")[:-1])
    except Exception:
        return 0


def getRole(interaction: discord.Interaction, role_id: int) -> None | discord.Role:
    if role_id == 0:
        return None
    role = interaction.guild.get_role(role_id)
    return role


def get_channel_id_from_mention(channel_mention: str) -> int:
    try:
        return int(channel_mention.replace("<#", "")[:-1])
    except Exception:
        return 0


def getVoiceChannel(interaction: discord.Interaction, channel_id: int) -> None | discord.VoiceChannel:
    if channel_id == 0:
        return None
    channel = interaction.guild.get_channel(channel_id)
    return channel if type(channel) == discord.VoiceChannel else None


def addWordsToBlacklist(words: list):
    configManager.getBlacklistedWords().extend(words)
    configManager.saveConfigJSON()



def getRoleIdFromRoles(roles: List[Role]) -> list:
    userRolesId = []
    for r in roles:
        userRolesId.append(r.id)
    return userRolesId

def getUserWarningLevel(user: discord.Member) -> int:
    lastIndex = 0
    for i in range(1, configManager.getWarningLevels()+1):
        warning_data: dict = configManager.getWarningDataForLevel(i)
        if len(warning_data) == 0:
            continue

        roles_id: list | None = warning_data.get("roles_id", None)
        userRolesId = getRoleIdFromRoles(user.roles)
        if roles_id is not None:
            hasAllRoles = False
            for role_id in roles_id:
                if role_id in userRolesId:
                    hasAllRoles = True
                else:
                    hasAllRoles = False
                    break
            if hasAllRoles and lastIndex < i:
                lastIndex = i
    return lastIndex


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

    usersId: list = res.get("users_id", None)
    userRestricted = False
    if usersId is not None:
        userRestricted = interaction.user.id not in usersId
        if userRestricted:
            reason += "user id;"

    userRoles = interaction.user.roles
    userRoleId = []
    for role in userRoles:
        userRoleId.append(role.id)
    anyRolesId: list = res.get("any_roles_id", None)
    if anyRolesId is not None:
        for rId in anyRolesId:
            if rId in userRoleId:
                userRestricted = False
                break
        if not userRestricted:
            reason += "any roles;"

    allRolesId: list = res.get("all_roles_id", None)
    if allRolesId is not None:
        hasAllRoles = False
        for roleId in allRolesId:
            if roleId in userRoleId:
                hasAllRoles = True
            else:
                hasAllRoles = False
                break

        if not hasAllRoles:
            reason += "all roles;"

    channels_id = res.get("channels_id", None)
    if channels_id is not None and not interaction.channel.id in channels_id:
        reason += "channel id;"

    return reason


def isUserRestrictedCtx(ctx: discord.ext.commands.context.Context, commandName: str) -> str:
    res = configManager.getCommandRestrictions(commandName)
    reason = ""
    if res.get("all", None) is not None:
        if res.get("all"):
            return reason
        else:
            reason += "all;"

    usersId: list = res.get("users_id", None)
    userRestricted = False
    if usersId is not None:
        userRestricted = ctx.author.id not in usersId
        if userRestricted:
            reason += "user id;"

    userRoles = ctx.author.roles
    anyRolesId: list = res.get("any_roles_id", None)
    userRoleId = []
    for role in userRoles:
        userRoleId.append(role.id)
    if anyRolesId is not None:
        for rId in anyRolesId:
            if rId in userRoleId:
                userRestricted = False
                break
        if not userRestricted:
            reason += "any roles;"

    allRolesId: list = res.get("all_roles_id", None)
    if allRolesId is not None:
        hasAllRoles = False
        for roleId in allRolesId:
            if roleId in userRoleId:
                hasAllRoles = True
            else:
                hasAllRoles = False
                break

        if hasAllRoles:
            reason += "all roles;"

    channels_id = res.get("channels_id", None)
    if channels_id is not None and not ctx.channel.id in channels_id:
        reason += "channel id;"

    return reason


async def handleRestricted(interaction: discord.Interaction, commandName: str) -> bool:
    reason = isUserRestricted(interaction, commandName)
    if len(reason) > 0:
        await handleMessage(interaction, commandName,
                            error_name=configManager.getRestrictedKey(),
                            placeholders={configManager.getReasonPlaceholder(): reason})

        return True
    return False


async def handleRestrictedCtx(ctx: discord.ext.commands.context.Context, commandName: str) -> bool:
    reason = isUserRestrictedCtx(ctx, commandName)
    if len(reason) > 0:
        await handleMessageCtx(ctx, commandName,
                               error_name=configManager.getRestrictedKey(),
                               placeholders={configManager.getReasonPlaceholder(): reason})

        return True
    return False
