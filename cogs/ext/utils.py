from __future__ import annotations

import discord
import os, sys, json
from discord.ext import commands
from discord import app_commands, Member
from cogs.ext.config_manager import ConfigManager

configManager = ConfigManager("config", "messages", "warnings")


async def setup(bot: commands.Bot):
    pass


"""
def setupCommandData(theClass):
    res = dict()
    for name, func in theClass.__dict__.items():
        if name.startswith("_"):
            continue
        cmd_data = configManager.getCommandData(name)
        if cmd_data is None:
            print("You miss-configure the command " + name)
            exit()

        res[name] = cmd_data
    return res

"""



async def sendResponse(interaction: discord.Interaction, command_name: str, message_key: str, placeholders: dict = dict()):
    message: str = configManager.getCommandMessage(command_name, message_key)
    embed = None
    if configManager.getEmbeds() is not None and message_key in configManager.getEmbeds():
        embed = buildEmbed(message_key, placeholders)

    if message is not None:
        for placeholder, v in placeholders.items():
            if configManager.isActivePlaceholder(placeholder):
                message = message.replace(placeholder, v)

    eph = configManager.getEphPlaceholder()

    try:
        await interaction.response.send_message(message, embed=embed,
                                                ephemeral=True
                                                if configManager.isActivePlaceholder(eph) and
                                                   (message is not None and eph is not None and eph in message)
                                                else False)
    except Exception:
        await interaction.channel.send(message, embed=embed,
                                       ephemeral=True
                                       if configManager.isActivePlaceholder(eph) and
                                          (message is not None and eph is not None and eph in message)
                                       else False)


def buildEmbed(message_key: str, placeholders: dict):
    try:
        data: dict = configManager.getEmbeds().get(message_key)

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
        return discord.Embed(description=e)


def getMember(interaction: discord.Interaction, member_id: int) -> Member | None:
    if member_id == 0:
        return None
    member = interaction.guild.get_member(member_id)
    return member


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


def addWarningToConfig(user_id: str, reason: str):
    configManager.warning_data[user_id] = reason
    configManager.saveWarningsJSON()


def removeWarningFromConfig(user_id: str):
    configManager.warning_data.pop(user_id)
    configManager.saveWarningsJSON()
