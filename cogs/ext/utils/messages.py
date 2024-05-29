from __future__ import annotations

import discord
from discord.ext import commands
import cogs.ext.utils.utils as utils
import cogs.ext.utils.buttons as buttons
import cogs.ext.utils.placeholders as placeholders_util


def isEmbedEph(embed: discord.Embed, eph: str) -> bool:
    return embed is not None and utils.configManager.isActivePlaceholder(eph) and eph in embed.title


def isMsgEph(msg, eph) -> bool:
    return utils.configManager.isActivePlaceholder(eph) and eph in msg


async def handleMessageResponse(msg: str | None, embed: discord.Embed | None, buttonView: discord.ui.View | None,
                                channel: discord.TextChannel | None, DMUser: discord.User | None, isEph: bool,
                                interaction: discord.Interaction = None,
                                ctx: discord.ext.commands.context.Context | None = None):
    if embed is not None:
        embed.title = embed.title.replace(utils.configManager.getEphPlaceholder(), "")
        if interaction is not None:
            await interaction.response.send_message(embed=embed, ephemeral=isEph)

            await interaction.channel.send(embed=embed)
        elif ctx is not None:
            await ctx.reply(embed=embed, ephemeral=isEph)

            await ctx.send(embed=embed)
        if channel is not None:
            await channel.send(embed=embed)
        if DMUser is not None:
            await DMUser.send(embed=embed)

    if msg is not None and len(msg.replace(" ", "")) > 0:
        msg = msg.replace(utils.configManager.getEphPlaceholder(), "")
        if interaction is not None:
            await interaction.response.send_message(msg, ephemeral=isEph)

            await interaction.channel.send(msg)
        elif ctx is not None:
            await ctx.reply(msg, ephemeral=isEph)

            await ctx.send(msg)
        if channel is not None:
            await channel.send(msg)
        if DMUser is not None:
            await DMUser.send(msg)

    if buttonView is not None:
        if interaction is not None:
            await interaction.response.send_message(view=buttonView(), ephemeral=isEph)

            await interaction.channel.send(view=buttonView())
        elif ctx is not None:
            await ctx.reply(view=buttonView(), ephemeral=isEph)

            await ctx.send(view=buttonView())
        if channel is not None:
            await channel.send(view=buttonView())
        if DMUser is not None:
            await DMUser.send(view=buttonView())


async def sendResponse(mainData: dict, DMUser: discord.User | None, interaction: discord.Interaction | None = None,
                       ctx: discord.ext.commands.context.Context | None = None):
    if len(mainData) == 0:
        raise Exception("No data given")

    eph = utils.configManager.getEphPlaceholder()
    if DMUser is None:
        if interaction is not None:
            DMUser = interaction.user
        elif ctx is not None:
            DMUser = ctx.author

    for messageName, data in mainData.items():
        messages: list = data.get("messages", [])
        embed: discord.Embed | None = data.get("embed", None)
        DMMessages: list = data.get("dm_messages", [])
        DMEmbeds: list = data.get("dm_embeds", [])
        DMButtons: list = data.get("dm_buttons", [])
        channelEmbeds: list = data.get("channel_embeds", [])
        channelMessages: list = data.get("channel_messages", [])
        channelButtons: list = data.get("channel_buttons", [])
        channel: discord.TextChannel | None = data.get("channel", None)
        buttonView: discord.ui.View | None = data.get("button", None)

        if interaction is None and ctx is None and channel is None:
            raise Exception("Expected valid text channel when there is no interaction! for message " + messageName)

        await handleMessageResponse(None, embed, None, channel, DMUser,
                                    isEmbedEph(embed, eph), interaction=interaction, ctx=ctx)

        for msg in messages:
            await handleMessageResponse(msg, None, None, channel, DMUser,
                                        isMsgEph(msg, eph), interaction=interaction, ctx=ctx)

        if channel is not None:
            for channelMessage in channelMessages:
                await handleMessageResponse(channelMessage, None, None, channel, DMUser,
                                            isMsgEph(channelMessage, eph), interaction=interaction, ctx=ctx)
            for channelEmbed in channelEmbeds:
                await handleMessageResponse(None, channelEmbed, None, channel, DMUser,
                                            isEmbedEph(channelEmbed, eph), interaction=interaction, ctx=ctx)
            for channelButton in channelButtons:
                await handleMessageResponse(None, None, buttonView, channel, DMUser,
                                            buttonView.is_active_placeholder, interaction=interaction, ctx=ctx)
                await channel.send(view=channelButton())

        if DMUser is not None:
            for DM in DMMessages:
                await handleMessageResponse(DM, None, None, channel, DMUser,
                                            isMsgEph(DM, eph), interaction=interaction, ctx=ctx)
            for DMEmbed in DMEmbeds:
                await handleMessageResponse(None, DMEmbed, None, channel, DMUser,
                                            isEmbedEph(DMEmbed, eph), interaction=interaction, ctx=ctx)
            for DMButton in DMButtons:
                await handleMessageResponse(None, None, DMButton, channel, DMUser,
                                            buttonView.is_active_placeholder, interaction=interaction, ctx=ctx)

        if buttonView is not None:
            await handleMessageResponse(None, None, buttonView, channel, DMUser,
                                        buttonView.is_active_placeholder, interaction=interaction, ctx=ctx)


async def MainBuild(bot: commands.Bot, commandName: str, executionPath: str, placeholders: dict,
                    interaction: discord.Interaction | None = None,
                    ctx: discord.ext.commands.context.Context | None = None):
    if bot is None:
        if interaction is not None:
            bot = interaction.client
        elif ctx is not None:
            bot = ctx.bot
    placeholders = placeholders_util.addDefaultPlaceholder(placeholders,
                                                           interaction=interaction, ctx=ctx)
    multiMessage = dict()
    allMessages = utils.configManager.getCommandData(commandName).get("message_names", [])
    if not isinstance(allMessages, list):
        raise Exception("`message_names` is not a list! Expected a list.")
    for msg in allMessages:
        print(msg)
        message: list = buildMessageData(commandName, msg, placeholders)
        (DM, DMEmbeds, DMButtons) = await buildDMData(bot, commandName, msg, executionPath, placeholders,
                                                      interaction=interaction, ctx=ctx)
        (builtChannelEmbeds, builtChannelMessages, channel, builtChannelButtons) = (
            await buildChannelData(bot, commandName, msg, placeholders, executionPath,
                                   None, interaction=interaction, ctx=ctx))

        multiMessage[msg] = {"messages": message,
                             "embed": await buildEmbed(bot, commandName, msg, executionPath, placeholders,
                                                       None, interaction=interaction, ctx=ctx),
                             "dm_messages": DM,
                             "dm_embeds": DMEmbeds,
                             "dm_buttons": DMButtons,
                             "channel_embeds": builtChannelEmbeds,
                             "channel_messages": builtChannelMessages,
                             "channel_buttons": builtChannelButtons,
                             "channel": channel,
                             "button": buttons.buildButtonData(bot, msg, placeholders)}

    return multiMessage


async def isCommandRestricted(bot: commands.Bot, commandName: str, executionPath: str,
                              interaction: discord.Interaction | None = None,
                              ctx: discord.ext.commands.context.Context | None = None) -> bool:
    if bot is None:
        if interaction is not None:
            bot = interaction.client
        elif ctx is not None:
            bot = ctx.bot

    if interaction is None and ctx is None:
        reason = ""
    else:
        reason = await utils.isUserRestricted(bot, commandName, executionPath, interaction=interaction, ctx=ctx)
    if len(reason.replace(" ", "")) > 0:
        return await handleMessage(bot, commandName, executionPath, DMUser=None,
                                   placeholders={utils.configManager.getReasonPlaceholder(): reason},
                                   interaction=interaction, ctx=ctx)
    return False


async def buildChannelData(bot: commands.Bot, commandName: str, message: str, placeholders: dict, executionPath: str,
                           error,
                           interaction: discord.Interaction | None = None,
                           ctx: discord.ext.commands.context.Context | None = None) -> tuple:
    if bot is None:
        if interaction is not None:
            bot = interaction.client
        elif ctx is not None:
            bot = ctx.bot
        else:
            return (None, None, None, None)
    channelMessages: list = utils.configManager.getMessagesByChannel(message).copy()
    channelEmbeds: list = utils.configManager.getEmbedsByChannel(message).copy()
    channelButtons: list = utils.configManager.getButtonsByChannel(message).copy()
    builtChannelEmbeds = []
    if len(channelEmbeds) > 0:
        for EmbedName in channelEmbeds:
            embed = await buildEmbed(bot, commandName, EmbedName, executionPath, placeholders, error,
                                     interaction=interaction, ctx=ctx)
            if embed is not None:
                builtChannelEmbeds.append(embed.copy())

    builtChannelMessages = []
    if len(channelMessages) > 0:
        for messageName in channelMessages:
            for msg in buildMessageData(commandName, messageName, placeholders):
                builtChannelMessages.append(msg)

    builtChannelButtons = []
    if len(channelButtons) > 0:
        for buttonName in channelButtons:
            button = buttons.buildButtonData(bot, buttonName, placeholders)
            if button is not None:
                builtChannelButtons.append(button)

    channelId: int = utils.configManager.getChannelIdByName(message)
    channel: discord.abc.GuildChannel | None = bot.get_channel(channelId)
    if channel is None:
        if interaction is not None:
            channel = interaction.channel
        elif ctx is not None:
            channel = ctx.channel
    if isinstance(channel, discord.TextChannel):
        return (builtChannelEmbeds, builtChannelMessages, channel, builtChannelButtons)

    if error is None:
        await handleError(bot, commandName, executionPath, "Text channel expected", placeholders=placeholders,
                          interaction=interaction, ctx=ctx)
    else:
        raise Exception("Text channel expected")

    return (None, None, None, None)


def buildMessageData(commandName: str, msg: str, placeholders: dict) -> list:
    message: list = utils.configManager.getCommandMessages(commandName, msg).copy()
    if len(message) > 0:
        for i in range(len(message)):
            message[i] = placeholders_util.usePlaceholders(message[i], placeholders)
    return message


async def buildDMData(bot: commands.Bot, command: str, msg: str, executionPath: str, placeholders: dict,
                      interaction: discord.Interaction | None = None,
                      ctx: discord.ext.commands.context.Context | None = None) -> tuple:
    if bot is None:
        if interaction is not None:
            bot = interaction.client
        elif ctx is not None:
            bot = ctx.bot
    DM: list = utils.configManager.getDMMessages(msg).copy()
    builtDMMessages = []
    if len(DM) > 0:
        for DMMessage in DM:
            for msg in buildMessageData(command, DMMessage, placeholders):
                builtDMMessages.append(msg)

    DMEmbeds: list = utils.configManager.getDMEmbeds(msg).copy()
    builtDMEmbeds = []
    if len(DMEmbeds) > 0:
        for embedName in DMEmbeds:
            embed = await buildEmbed(bot, command, embedName, executionPath, placeholders, None,
                                     interaction=interaction, ctx=ctx)
            if embed is not None:
                builtDMEmbeds.append(embed.copy())

    DMButtons: list = utils.configManager.getDMViews(msg).copy()
    builtDMButtons = []
    if len(DMButtons) > 0:
        for DMButton in DMButtons:
            button = buttons.buildButtonData(bot, DMButton, placeholders)
            if button is not None:
                builtDMButtons.append(button)

    return (builtDMMessages, builtDMEmbeds, builtDMButtons)


async def MainBuildError(bot: commands.Bot, commandName: str, errorPath: str, error,
                         placeholders: dict, interaction: discord.Interaction = None,
                         ctx: discord.ext.commands.context.Context | None = None):
    if bot is None:
        if interaction is not None:
            bot = interaction.client
        elif ctx is not None:
            bot = ctx.bot

    if len(errorPath.replace(" ", "")) > 0:
        message: list = buildMessageData(commandName, errorPath, placeholders)
        (DM, DMEmbeds, DMButtons) = await buildDMData(bot, commandName, errorPath, errorPath, placeholders,
                                                      interaction=interaction, ctx=ctx)
        (builtChannelEmbeds, builtChannelMessages, channel, builtChannelButtons) = (
            await buildChannelData(bot, commandName, message=errorPath, placeholders=placeholders,
                                   executionPath=errorPath,
                                   error=error,
                                   interaction=interaction, ctx=ctx))

        return {errorPath: {"messages": message,
                            "embed": await buildEmbed(bot, commandName, errorPath, errorPath, placeholders, error,
                                                      interaction=interaction, ctx=ctx),
                            "dm_messages": DM,
                            "dm_embeds": DMEmbeds,
                            "dm_buttons": DMButtons,
                            "channel_embeds": builtChannelEmbeds,
                            "channel_messages": builtChannelMessages,
                            "channel_buttons": builtChannelButtons,
                            "channel": channel,
                            "button": buttons.buildButtonData(bot, errorPath, placeholders)}}
    return dict()


async def buildEmbed(bot: commands.Bot, command: str, message_key: str, executionPath: str, placeholders: dict, error,
                     interaction: discord.Interaction | None = None,
                     ctx: discord.ext.commands.context.Context | None = None) -> discord.Embed | None:
    try:
        data: dict | None = utils.configManager.getCommandEmbeds(command, message_key)
        if data is None:
            return None

        embed = discord.Embed()
        for key, value in data.items():
            if key == utils.configManager.getEmbedTitle():
                embed.title = placeholders_util.usePlaceholders(value, placeholders)
            elif key == utils.configManager.getEmbedAuthorName():
                embed.author.name = placeholders_util.usePlaceholders(value, placeholders)
            elif key == utils.configManager.getEmbedAuthorUrl():
                embed.author.url = placeholders_util.usePlaceholders(value, placeholders)
            elif key == utils.configManager.getEmbedAuthorIconUrl():
                embed.author.icon_url = placeholders_util.usePlaceholders(value, placeholders)
            elif key == utils.configManager.getEmbedFooter():
                embed.footer.text = placeholders_util.usePlaceholders(value, placeholders)
            elif key == utils.configManager.getEmbedFooterIconUrl():
                embed.footer.icon_url = placeholders_util.usePlaceholders(value, placeholders)
            elif key == utils.configManager.getEmbedImageUrl():
                embed.image.url = placeholders_util.usePlaceholders(value, placeholders)
            elif key == utils.configManager.getEmbedDescription():
                embed.description = placeholders_util.usePlaceholders(value, placeholders)
            elif key == utils.configManager.getEmbedColor():
                value = placeholders_util.usePlaceholders(value, placeholders)
                embed.colour = discord.Colour.random() \
                    if value == "random" or len(value) == 0 \
                    else discord.Colour.from_str(value)
            elif key == utils.configManager.getEmbedFields():
                notinlinePlaceholder = utils.configManager.getNotInLinePlaceholder()
                if not isinstance(value, dict):
                    raise Exception("Embed " + message_key +
                                    " needs fields as map: Example (" + notinlinePlaceholder +
                                    " placeholder is optional): " +
                                    "'" + utils.configManager.getEmbedFields() + "': {'FieldName': 'FieldValue " +
                                    notinlinePlaceholder + "'}")
                for k, v in data.get(utils.configManager.getEmbedFields()).items():
                    if notinlinePlaceholder in v and utils.configManager.isActivePlaceholder(notinlinePlaceholder):
                        embed.add_field(name=k, value=v, inline=False)
                    else:
                        embed.add_field(name=k, value=v)

        return embed

    except Exception as e:
        if error is None:
            await handleError(bot, command, executionPath, e, placeholders=placeholders,
                              interaction=interaction, ctx=ctx)
        else:
            raise Exception(e)
        return None


async def handleMessage(bot: commands.Bot, commandName: str, executionPath: str, placeholders: dict = dict(),
                        DMUser: discord.User | None = None,
                        interaction: discord.Interaction | None = None,
                        ctx: discord.ext.commands.context.Context | None = None) -> bool:
    try:
        await sendResponse(await MainBuild(bot, commandName, executionPath=executionPath, placeholders=placeholders,
                                           interaction=interaction, ctx=ctx), DMUser=DMUser, interaction=interaction,
                           ctx=ctx)
        return True
    except Exception as e:
        return await handleError(bot, commandName, executionPath, e, placeholders=placeholders,
                                 interaction=interaction, ctx=ctx)


async def handleError(bot: commands.Bot, commandName: str, executionPath: str, error, placeholders: dict = dict(),
                      interaction: discord.Interaction | None = None,
                      ctx: discord.ext.commands.context.Context | None = None) -> bool:
    if error is not None:
        placeholders[utils.configManager.getErrorPlaceholder()] = error
        placeholders[utils.configManager.getErrorPathPlaceholder()] = executionPath
        try:
            await sendResponse(
                await MainBuildError(bot, commandName, executionPath, error, placeholders,
                                     interaction=interaction, ctx=ctx),
                DMUser=None)
            return True
        except Exception as ex:
            if utils.configManager.isPrintError():
                print("original error:", error, "follow up error:", ex)
            return False


async def handleInvalidMember(bot: commands.Bot, command: str, executionPath: str, error,
                              interaction: discord.Interaction | None = None,
                              ctx: discord.ext.commands.context.Context | None = None) -> bool:
    return await handleError(bot, command, executionPath, error,
                             placeholders={
                                 utils.configManager.getInvalidUsernamePlaceholder(): error},
                             interaction=interaction, ctx=ctx)


async def handleInvalidRole(bot: commands.Bot, command: str, executionPath: str, error,
                            interaction: discord.Interaction | None = None,
                            ctx: discord.ext.commands.context.Context | None = None) -> bool:
    return await handleError(bot, command, executionPath, error,
                             placeholders={utils.configManager.getInvalidUsernamePlaceholder(): error},
                             interaction=interaction, ctx=ctx)


async def handleInvalidArg(bot: commands.Bot, command: str, executionPath: str, error,
                           interaction: discord.Interaction | None = None,
                           ctx: discord.ext.commands.context.Context | None = None) -> bool:
    return await handleError(bot, command, executionPath, error,
                             placeholders={utils.configManager.getInvalidArgumentPlaceholder(): error},
                             interaction=interaction, ctx=ctx)


async def handleInvalidChannels(bot: commands.Bot, command: str, executionPath: str, error,
                                interaction: discord.Interaction | None = None,
                                ctx: discord.ext.commands.context.Context | None = None) -> bool:
    return await handleError(bot, command, executionPath, error,
                             placeholders={utils.configManager.getInvalidChannelPlaceholder(): error},
                             interaction=interaction, ctx=ctx)
