import discord
import os, sys, json
from discord.ext import commands
from discord import app_commands, Member
from cogs.ext.config_manager import ConfigManager

configManager = ConfigManager("configs/config", "configs/messages",
                              "configs/warnings", "configs/commands")


async def setup(bot: commands.Bot):
    pass


async def sendResponse(interaction: discord.Interaction, message: str, embed: discord.Embed):
    if len(message.replace(" ", "")) == 0:
        message = None

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


def buildMessages(command_name: str, error_name: str = "", placeholders: dict = dict()):
    if len(error_name.replace(" ", "")) > 0:
        error_embed = buildEmbed(command_name, error_name, placeholders)
        message: str = configManager.getCommandMessages(command_name, error_name)
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


async def handleMessage(interaction: discord.Interaction, command_name: str, error_name: str = "",
                        placeholders: dict = dict()):
    await sendResponse(interaction, *buildMessages(command_name, error_name, placeholders))


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


def addWarningToConfig(user_id: str, reason: str):
    configManager.warning_data[user_id] = reason
    configManager.saveWarningsJSON()


def removeWarningFromConfig(user_id: str):
    configManager.warning_data.pop(user_id)
    configManager.saveWarningsJSON()
