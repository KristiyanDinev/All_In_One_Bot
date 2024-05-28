from __future__ import annotations

import discord
from discord.ext import commands
import cogs.ext.utils.utils as utils
import cogs.ext.utils.buttons as buttons
import cogs.ext.utils.leveling as leveling
import cogs.ext.utils.placeholders as placeholders_util


def isEmbedEph(embed, eph) -> bool:
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

    if interaction is None and ctx is None:
        raise Exception("Interaction given")

    eph = utils.configManager.getEphPlaceholder()
    if DMUser is None and interaction is not None:
        DMUser = interaction.user

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


def MainBuild(commandName: str, executionPath: str, placeholders: dict, interaction: discord.Interaction = None,
              ctx: discord.ext.commands.context.Context | None = None):
    placeholders = placeholders_util.addDefaultPlaceholder(placeholders,
                                                           interaction=interaction, ctx=ctx)
    multiMessage = dict()
    bot = interaction.client if interaction is not None else ctx.bot
    allMessages = utils.configManager.getCommandData(commandName).get("message_names", [])
    if not isinstance(allMessages, list):
        raise Exception("`message_names` is not a list! Expected a list.")
    for msg in allMessages:
        message: list = buildMessageData(commandName, msg, placeholders)
        (DM, DMEmbeds, DMButtons) = buildDMData(bot, commandName, msg, placeholders)

        if interaction is not None:
            (builtChannelEmbeds, builtChannelMessages, channel, builtChannelButtons) = (
                buildChannelData(commandName, msg, placeholders, executionPath, None, interaction=interaction, ctx=ctx))

        elif ctx is not None:
            (builtChannelEmbeds, builtChannelMessages, channel, builtChannelButtons) = (
                buildChannelData(commandName, msg, placeholders, executionPath, None, interaction=interaction, ctx=ctx))

        else:
            (builtChannelEmbeds, builtChannelMessages, channel, builtChannelButtons) = (
                buildChannelData(commandName, msg, placeholders, executionPath, None, interaction=interaction, ctx=ctx))

        multiMessage[msg] = {"messages": message,
                             "embed": buildEmbed(commandName, msg, executionPath, placeholders,
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


async def isCommandRestricted(commandName: str, executionPath: str, interaction: discord.Interaction | None = None,
                              ctx: discord.ext.commands.context.Context | None = None) -> bool:
    if interaction is not None:
        reason = utils.isUserRestricted(interaction, commandName)
    elif ctx is not None:
        reason = utils.isUserRestrictedCtx(ctx, commandName)
    else:
        reason = ""
    if len(reason.replace(" ", "")) > 0:
        return await handleMessage(commandName, executionPath, DMUser=None,
                                   placeholders={utils.configManager.getReasonPlaceholder(): reason},
                                   interaction=interaction, ctx=ctx)
    return False


async def buildChannelData(commandName: str, msg: str, placeholders: dict, executionPath: str, error,
                           interaction: discord.Interaction = None,
                           ctx: discord.ext.commands.context.Context | None = None) -> tuple:
    bot = interaction.client if interaction is not None else ctx.bot
    channelMessages: list = utils.configManager.getMessagesByChannel(msg).copy()
    channelEmbeds: list = utils.configManager.getEmbedsByChannel(msg).copy()
    channelButtons: list = utils.configManager.getButtonsByChannel(msg).copy()
    builtChannelEmbeds = []
    if len(channelEmbeds) > 0:
        for EmbedName in channelEmbeds:
            embed = buildEmbed(commandName, EmbedName, executionPath, placeholders, error,
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

    channelId: int = utils.configManager.getChannelIdByName(msg)
    channel: discord.abc.GuildChannel | None = bot.get_channel(channelId)
    if channel is None:
        if interaction is not None:
            channel = interaction.channel
        elif ctx is not None:
            channel = ctx.channel
    if isinstance(channel, discord.TextChannel):
        return (builtChannelEmbeds, builtChannelMessages, channel, builtChannelButtons)

    if error is None:
        await handleError(commandName, executionPath, "Text channel expected", placeholders=placeholders,
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


def buildDMData(bot: commands.Bot, command: str, msg: str, placeholders: dict) -> tuple:
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
            embed = buildEmbed(command, embedName, placeholders)
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



def MainBuildError(commandName: str, errorPath: str, error,
                   placeholders: dict, interaction: discord.Interaction = None,
                   ctx: discord.ext.commands.context.Context | None = None):
    bot = interaction.client if interaction is not None else ctx.bot
    if len(errorPath.replace(" ", "")) > 0:
        message: list = buildMessageData(commandName, errorPath, placeholders)
        (DM, DMEmbeds, DMButtons) = buildDMData(bot, commandName, errorPath, placeholders)
        (builtChannelEmbeds, builtChannelMessages, channel, builtChannelButtons) = (
            buildChannelData(commandName, errorPath, placeholders, errorPath, error, interaction=interaction, ctx=ctx))

        return {errorPath: {"messages": message,
                            "embed": buildEmbed(commandName, errorPath, errorPath, placeholders, error,
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


async def buildEmbed(command: str, message_key: str, executionPath: str, placeholders: dict, error,
                     interaction: discord.Interaction | None = None,
                     ctx: discord.ext.commands.context.Context | None = None, ) -> discord.Embed | None:
    try:
        data: dict = utils.configManager.getCommandEmbeds(command, message_key)
        title: str = str(data.get(utils.configManager.getEmbedTitle(), utils.configManager.getEmbedTitle()))
        authorName: str = str(
            data.get(utils.configManager.getEmbedAuthorName(), utils.configManager.getEmbedAuthorName()))
        authorUrl: str = str(
            data.get(utils.configManager.getEmbedAuthorUrl(), utils.configManager.getEmbedAuthorUrl()))
        authorIconUrl: str = str(
            data.get(utils.configManager.getEmbedAuthorIconUrl(), utils.configManager.getEmbedAuthorIconUrl()))
        footerText: str = str(data.get(utils.configManager.getEmbedFooter(), utils.configManager.getEmbedFooter()))
        footerIconUrl: str = str(
            data.get(utils.configManager.getEmbedFooterIconUrl(), utils.configManager.getEmbedFooterIconUrl()))
        imageUrl: str = str(data.get(utils.configManager.getEmbedImageUrl(), utils.configManager.getEmbedImageUrl()))
        desc: str = str(data.get(utils.configManager.getEmbedDescription(), utils.configManager.getEmbedDescription()))
        colour: str = str(data.get(utils.configManager.getEmbedColor(), utils.configManager.getEmbedColor()))

        title = placeholders_util.usePlaceholders(title, placeholders)
        authorName = placeholders_util.usePlaceholders(authorName, placeholders)
        authorUrl = placeholders_util.usePlaceholders(authorUrl, placeholders)
        authorIconUrl = placeholders_util.usePlaceholders(authorIconUrl, placeholders)
        footerText = placeholders_util.usePlaceholders(footerText, placeholders)
        footerIconUrl = placeholders_util.usePlaceholders(footerIconUrl, placeholders)
        imageUrl = placeholders_util.usePlaceholders(imageUrl, placeholders)
        desc = placeholders_util.usePlaceholders(desc, placeholders)

        embed = discord.Embed(title=title,
                              colour=discord.Colour.random()
                              if colour == "random" or len(colour) == 0 else discord.Colour.from_str(colour),
                              description=desc)

        embed.set_author(name=authorName,
                         url=authorUrl,
                         icon_url=authorIconUrl)

        embed.set_footer(text=footerText,
                         icon_url=footerIconUrl)

        embed.set_image(url=imageUrl)

        for k, v in data.get(utils.configManager.getEmbedFields()).items():
            notinlinePlaceholder = utils.configManager.getNotInLinePlaceholder()
            if notinlinePlaceholder in v and utils.configManager.isActivePlaceholder(notinlinePlaceholder):
                embed.add_field(name=k, value=v, inline=False)
            else:
                embed.add_field(name=k, value=v)

        return embed.copy()

    except Exception as e:
        if error is None:
            await handleError(command, executionPath, e, placeholders=placeholders, interaction=interaction, ctx=ctx)
        else:
            raise Exception(e)
        return None


async def handleMessage(commandName: str, executionPath: str, placeholders: dict = dict(),
                        DMUser: discord.User | None = None,
                        interaction: discord.Interaction | None = None,
                        ctx: discord.ext.commands.context.Context | None = None) -> bool:
    try:
        await sendResponse(MainBuild(commandName, placeholders, interaction=interaction, ctx=ctx),
                           DMUser, interaction=interaction, ctx=ctx)
    except Exception as e:
        return await handleError(commandName, executionPath, e, placeholders=placeholders,
                                 interaction=interaction, ctx=ctx)


async def handleError(commandName: str, executionPath: str, error, placeholders: dict = dict(),
                      interaction: discord.Interaction | None = None,
                      ctx: discord.ext.commands.context.Context | None = None) -> bool:
    if error is not None:
        placeholders[utils.configManager.getErrorPlaceholder()] = error
        placeholders[utils.configManager.getErrorPathPlaceholder()] = executionPath
        try:
            await sendResponse(
                MainBuildError(commandName, executionPath, error, placeholders, interaction=interaction, ctx=ctx),
                DMUser=None)
            return True
        except Exception as ex:
            if utils.configManager.isPrintError():
                print("original error:", error, "follow up error:", ex)
            return False


async def handleInvalidMember(command: str, executionPath: str, error, interaction: discord.Interaction | None = None,
                              ctx: discord.ext.commands.context.Context | None = None) -> bool:
    return await handleError(command, executionPath, error,
                             placeholders={
                                 utils.configManager.getInvalidUsernamePlaceholder(): error},
                             interaction=interaction, ctx=ctx)


async def handleInvalidRole(command: str, executionPath: str, error, interaction: discord.Interaction | None = None,
                            ctx: discord.ext.commands.context.Context | None = None) -> bool:
    return await handleError(command, executionPath, error,
                             placeholders={utils.configManager.getInvalidUsernamePlaceholder(): error},
                             interaction=interaction, ctx=ctx)


async def handleInvalidArg(command: str, executionPath: str, error, interaction: discord.Interaction | None = None,
                           ctx: discord.ext.commands.context.Context | None = None) -> bool:
    return await handleError(command, executionPath, error,
                             placeholders={utils.configManager.getInvalidArgumentPlaceholder(): error},
                             interaction=interaction, ctx=ctx)


async def handleInvalidChannels(command: str, executionPath: str, error, interaction: discord.Interaction | None = None,
                                ctx: discord.ext.commands.context.Context | None = None) -> bool:
    return await handleError(command, executionPath, error,
                             placeholders={utils.configManager.getInvalidChannelPlaceholder(): error},
                             interaction=interaction, ctx=ctx)
