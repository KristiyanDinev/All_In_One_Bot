from __future__ import annotations

import discord
from discord.ext import commands
import cogs.ext.utils.utils as utils
import cogs.ext.utils.buttons as buttons
import cogs.ext.utils.leveling as leveling
import cogs.ext.utils.placeholders as placeholders_util


async def handleMessageResponse(msg: str | None, embed: discord.Embed | None, buttonView: discord.ui.View | None,
                                channel: discord.TextChannel | None, isEph: bool,
                                interaction: discord.Interaction = None,
                                ctx: discord.ext.commands.context.Context | None = None):
    if embed is not None:
        embed.title = embed.title.replace(utils.configManager.getEphPlaceholder(), "")
        if interaction is not None:
            try:
                await interaction.response.send_message(embed=embed, ephemeral=isEph)

            except Exception:
                try:
                    await interaction.channel.send(embed=embed)
                except Exception:
                    pass

        elif ctx is not None:
            try:
                await ctx.reply(embed=embed, ephemeral=isEph)

            except Exception:
                try:
                    await ctx.send(embed=embed)
                except Exception:
                    pass

        if channel is not None:
            try:
                await channel.send(embed=embed)
            except Exception:
                pass

    if msg is not None and len(msg.replace(" ", "")) > 0:
        msg = msg.replace(utils.configManager.getEphPlaceholder(), "")
        if interaction is not None:
            try:
                await interaction.response.send_message(msg, ephemeral=isEph)

            except Exception:
                try:
                    await interaction.channel.send(msg)
                except Exception:
                    pass

        elif ctx is not None:
            try:
                await ctx.reply(msg, ephemeral=isEph)

            except Exception:
                try:
                    await ctx.send(msg)
                except Exception:
                    pass

        if channel is not None:
            try:
                await channel.send(msg)
            except Exception:
                pass

    if buttonView is not None:
        if interaction is not None:
            try:
                await interaction.response.send_message(view=buttonView(), ephemeral=isEph)

            except Exception:
                try:
                    await interaction.channel.send(view=buttonView())
                except Exception:
                    pass

        elif ctx is not None:
            try:
                await ctx.reply(view=buttonView(), ephemeral=isEph)

            except Exception:
                try:
                    await ctx.send(view=buttonView())
                except Exception:
                    pass

        if channel is not None:
            try:
                await channel.send(view=buttonView())
            except Exception:
                pass


async def sendResponse(interaction: discord.Interaction, mainData: dict, DMUser: discord.User):
    if len(mainData) == 0:
        return
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

        await handleMessageResponse(None, embed, None, None, embed is not None
                                    and utils.configManager.isActivePlaceholder(eph)
                                    and eph in embed.title, interaction=interaction)

        for msg in messages:
            await handleMessageResponse(msg, None, None, None,
                                        utils.configManager.isActivePlaceholder(eph)
                                        and eph in msg, interaction=interaction)
        if DMUser is not None:
            for DM in DMMessages:
                await DMUser.send(DM)
            for DMEmbed in DMEmbeds:
                await DMUser.send(embed=DMEmbed)
            for DMButton in DMButtons:
                await DMUser.send(view=DMButton())

        if channel is not None:
            try:
                for channelMessage in channelMessages:
                    await channel.send(channelMessage)
            except Exception:
                pass
            try:
                for channelEmbed in channelEmbeds:
                    await channel.send(embed=channelEmbed)
            except Exception:
                pass
            try:
                for channelButton in channelButtons:
                    await channel.send(view=channelButton())
            except Exception:
                pass

        if buttonView is not None:
            await handleMessageResponse(None, None, buttonView, None,
                                        buttonView.is_active_placeholder, interaction=interaction)


async def sendResponseCtx(ctx: discord.ext.commands.context.Context | None, mainData: dict, DMUser: discord.User):
    if len(mainData) == 0:
        return
    eph = utils.configManager.getEphPlaceholder()
    if DMUser is None and ctx is not None:
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

        await handleMessageResponse(None, embed, None, None, embed is not None
                                    and utils.configManager.isActivePlaceholder(eph)
                                    and eph in embed.title, ctx=ctx)

        for msg in messages:
            await handleMessageResponse(msg, None, None,
                                        None, utils.configManager.isActivePlaceholder(eph)
                                        and eph in msg, ctx=ctx)

        if DMUser is not None:
            for DMEmb in DMEmbeds:
                await DMUser.send(embed=DMEmb)

            for DM in DMMessages:
                await DMUser.send(DM)

            for DMButton in DMButtons:
                await DMUser.send(view=DMButton())

        if channel is not None:
            try:
                for channelEmbed in channelEmbeds:
                    await channel.send(embed=channelEmbed)
            except Exception:
                pass
            try:
                for channelMessage in channelMessages:
                    await channel.send(channelMessage)
            except Exception:
                pass
            try:
                for channelButton in channelButtons:
                    await channel.send(view=channelButton())
            except Exception:
                pass

        if buttonView is not None:
            await handleMessageResponse(None, None, buttonView,
                                        None, buttonView.is_active_placeholder, ctx=ctx)


async def handleMessage(interaction: discord.Interaction, commandName: str, errorPath: str = "",
                        placeholders: dict = dict(), DMUser: discord.User = None):
    mainData: dict = MainBuild(commandName, errorPath, placeholders, interaction=interaction)
    await sendResponse(interaction, mainData, DMUser)


async def handleMessageCtx(bot: commands.Bot, ctx: discord.ext.commands.context.Context | None, commandName: str,
                           errorName: str = "",
                           placeholders: dict = dict(), DMUser: discord.User = None):
    mainData: dict = MainBuild(bot, commandName, errorName, placeholders, ctx=ctx)
    await sendResponseCtx(ctx, mainData, DMUser)


async def handleInvalidMember(bot: commands.Bot, interaction: discord.Interaction, command: str):
    await handleMessage(bot, interaction, command,
                        errorPath=utils.configManager.getInvalidMemberKey(),
                        placeholders={
                            utils.configManager.getInvalidUsernamePlaceholder(): })


async def handleInvalidRole(bot: commands.Bot, interaction: discord.Interaction, command: str):
    await handleMessage(bot, interaction, command,
                        errorPath=utils.configManager.getInvalidRoleKey(),
                        placeholders={
                            utils.configManager.getInvalidRolePlaceholder(): })


async def handleInvalidArg(bot: commands.Bot, interaction: discord.Interaction, command: str):
    await handleMessage(bot, interaction, command,
                        errorPath=utils.configManager.getInvalidArgsKey(),
                        placeholders={utils.configManager.getInvalidArgumentPlaceholder(): })


async def handleInvalidChannels(bot: commands.Bot, interaction: discord.Interaction, command: str):
    await handleMessage(bot, interaction, command,
                        errorPath=utils.configManager.getInvalidChannelKey(),
                        placeholders={
                            utils.configManager.getInvalidChannelPlaceholder(): })



async def handleErrors(interaction: discord.Interaction, command: str, error, path: str, placeholders: dict):
    placeholders[utils.configManager.getErrorPlaceholder()] = error
    placeholders[utils.configManager.getErrorPathPlaceholder()] = path
    await handleMessage(interaction, command,
                        errorPath=path,
                        placeholders=placeholders)



def handleMultipleMessages(bot: commands.Bot, commandName: str,
                           placeholders: dict, interaction: discord.Interaction = None,
                           ctx: discord.ext.commands.context.Context | None = None):
    multiMessage = dict()
    for msg in utils.configManager.getCommandData(commandName).get("message_names", []):
        message: list = buildMessageData(commandName, msg, placeholders)
        (DM, DMEmbeds, DMButtons) = buildDMData(bot, commandName, msg, placeholders)

        if interaction is not None:
            (builtChannelEmbeds, builtChannelMessages, channel, builtChannelButtons) = (
                buildChannelData(bot, commandName, msg, placeholders, interaction=interaction))

        elif ctx is not None:
            (builtChannelEmbeds, builtChannelMessages, channel, builtChannelButtons) = (
                buildChannelData(bot, commandName, msg, placeholders, ctx=ctx))

        else:
            (builtChannelEmbeds, builtChannelMessages, channel, builtChannelButtons) = (
                buildChannelData(bot, commandName, msg, placeholders))

        multiMessage[msg] = {"messages": message,
                             "embed": buildEmbed(commandName, msg, placeholders),
                             "dm_messages": DM,
                             "dm_embeds": DMEmbeds,
                             "dm_buttons": DMButtons,
                             "channel_embeds": builtChannelEmbeds,
                             "channel_messages": builtChannelMessages,
                             "channel_buttons": builtChannelButtons,
                             "channel": channel,
                             "button": buttons.buildButtonData(bot, msg, placeholders)}

    return multiMessage


async def handleRestricted(bot: commands.Bot, interaction: discord.Interaction, commandName: str) -> bool:
    reason = utils.isUserRestricted(interaction, commandName)
    if len(reason) > 0:
        await handleMessage(bot, interaction, commandName,
                            errorPath=utils.configManager.getRestrictedKey(),
                            placeholders={utils.configManager.getReasonPlaceholder(): reason})

        return True
    return False


async def handleRestrictedCtx(bot: commands.Bot, ctx: discord.ext.commands.context.Context, commandName: str) -> bool:
    reason = utils.isUserRestrictedCtx(ctx, commandName)
    if len(reason) > 0:
        await handleMessageCtx(bot, ctx, commandName,
                               errorName=utils.configManager.getRestrictedKey(),
                               placeholders={utils.configManager.getReasonPlaceholder(): reason})

        return True
    return False


def handleUserLevelingOnMessage(user: discord.Member):
    maxLevel = leveling.getUserLevel(user, True)
    minLevel = leveling.getUserLevel(user, False)
    currentLevel = utils.configManager.getUserLevel(user.id)
    nextLevel = currentLevel + 1
    totalXP = utils.configManager.getUserXP(user.id) + utils.configManager.getXPPerMessages()

    if minLevel > currentLevel or currentLevel > maxLevel or maxLevel == minLevel:
        utils.configManager.setUserLevel(user.id, minLevel)
        utils.configManager.setUserXP(user.id, utils.configManager.getLevelXP(minLevel))
        utils.configManager.saveLevelJSON()
        return

    utils.configManager.setUserXP(user.id, totalXP)
    if totalXP >= utils.configManager.getLevelXP(nextLevel) and minLevel <= nextLevel <= maxLevel:
        utils.configManager.setUserLevel(user.id, nextLevel)

    utils.configManager.saveLevelJSON()


def buildChannelData(bot: commands.Bot, commandName: str, msg: str, placeholders: dict,
                     interaction: discord.Interaction = None,
                     ctx: discord.ext.commands.context.Context | None = None) -> tuple:
    channelMessages: list = utils.configManager.getMessagesByChannel(msg).copy()
    channelEmbeds: list = utils.configManager.getEmbedsByChannel(msg).copy()
    channelButtons: list = utils.configManager.getButtonsByChannel(msg).copy()
    builtChannelEmbeds = []
    if len(channelEmbeds) > 0:
        for EmbedName in channelEmbeds:
            embed = buildEmbed(commandName, EmbedName, placeholders)
            if embed is not None:
                builtChannelEmbeds.append(embed.copy())

    builtChannelMessages = []
    if len(channelMessages) > 0:
        for messageName in channelMessages:
            for msg in  buildMessageData(commandName, messageName, placeholders):
                builtChannelMessages.append(msg)


    builtChannelButtons = []
    if len(channelButtons) > 0:
        for buttonName in channelButtons:
            button = buttons.buildButtonData(bot, buttonName, placeholders)
            if button is not None:
                builtChannelButtons.append(button)

    channelId: int = utils.configManager.getChannelIdByName(msg)

    try:
        if bot is None:
            return (builtChannelEmbeds, builtChannelMessages, None, builtChannelButtons)

        channel: discord.abc.GuildChannel | None = bot.get_channel(channelId)
        if channel is None:
            if interaction is not None:
                channel = interaction.channel
            elif ctx is not None:
                channel = ctx.channel

        if type(channel) != discord.TextChannel:
            raise Exception()

        return (builtChannelEmbeds, builtChannelMessages, channel, builtChannelButtons)

    except Exception:
        return (builtChannelEmbeds, builtChannelMessages, None, builtChannelButtons)


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


def handleErrorMainBuild(commandName: str, errorPath: str,
                         placeholders: dict, interaction: discord.Interaction = None,
                         ctx: discord.ext.commands.context.Context | None = None):
    if len(errorPath.replace(" ", "")) > 0:




        message: list = buildMessageData(commandName, errorPathMsg, placeholders)
        (DM, DMEmbeds, DMButtons) = buildDMData(interaction.client, commandName, errorPathMsg, placeholders)
        (builtChannelEmbeds, builtChannelMessages, channel, builtChannelButtons) = (
            buildChannelData(commandName, errorPath, placeholders, interaction=interaction, ctx=ctx))

        return {errorPath: {"messages": message,
                            "embed": buildEmbed(commandName, errorPath, placeholders),
                            "dm_messages": DM,
                            "dm_embeds": DMEmbeds,
                            "dm_buttons": DMButtons,
                            "channel_embeds": builtChannelEmbeds,
                            "channel_messages": builtChannelMessages,
                            "channel_buttons": builtChannelButtons,
                            "channel": channel,
                            "button": buttons.buildButtonData(bot, errorPath, placeholders)}}
    return dict()


def MainBuild(commandName: str, errorPath: str = "", placeholders: dict = dict(),
              interaction: discord.Interaction = None,
              ctx: discord.ext.commands.context.Context | None = None) -> dict:
    placeholders = placeholders_util.addDefaultPlaceholder(placeholders, interaction=interaction, ctx=ctx)
    errorData = handleErrorMainBuild(commandName, errorPath, placeholders,
                                     interaction=interaction, ctx=ctx)
    return handleMultipleMessages(bot, commandName, placeholders,
                                  interaction=interaction, ctx=ctx) if len(errorData) == 0 else errorData


async def buildEmbed(interaction: discord.Interaction, command: str,
                     message_key: str, placeholders: dict) -> discord.Embed | None:
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
        await handleErrors(interaction, command, e, command+":"+message_key, placeholders)
        return None




