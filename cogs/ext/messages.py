from cogs.ext.imports import *

def isEmbedEph(embed: discord.Embed, eph: str) -> bool:
    return embed is not None and utils.configManager.isActivePlaceholder(eph) and eph in embed.title


def isMsgEph(msg, eph) -> bool:
    return utils.configManager.isActivePlaceholder(eph) and eph in msg


async def handleMessageResponse(msg: str | None, embed: discord.Embed | None, buttonView: discord.ui.View | None,
                                channel: discord.TextChannel | None, DMUser: discord.User | None, isEph: bool,
                                interaction: discord.Interaction | None = None,
                                ctx: discord.ext.commands.context.Context | None = None):
    if embed is not None:
        embed.title = embed.title.replace(utils.configManager.getEphPlaceholder(), "")
    hasMessage = msg is not None and len(msg.replace(" ", "")) > 0
    if hasMessage:
        msg = msg.replace(utils.configManager.getEphPlaceholder(), "")
    if interaction is not None and not interaction.is_expired():
        if interaction.is_done():
            if embed is not None:
                if interaction.is_done():
                    await interaction.channel.send(embed=embed)
            if hasMessage:
                await interaction.response.send_message(msg, ephemeral=isEph)
            if buttonView is not None:
                await interaction.channel.send(view=buttonView())
        else:
            if embed is not None:
                embed.title = embed.title.replace(utils.configManager.getEphPlaceholder(), "")
                await interaction.response.send_message(embed=embed, ephemeral=isEph)
            if hasMessage:
                await interaction.response.send_message(msg, ephemeral=isEph)
            if buttonView is not None:
                await interaction.response.send_message(view=buttonView(), ephemeral=isEph)
    if ctx is not None:
        hasReplied = False
        async for message in ctx.channel.history(after=ctx.message, limit=100):
            if (message.reference and message.reference.message_id == ctx.message.id and
                    message.author.id == ctx.bot.user.id):
                hasReplied = True
                break
        if hasReplied:
            if embed is not None:
                await ctx.send(embed=embed)
            if hasMessage:
                await ctx.send(msg)
            if buttonView is not None:
                await ctx.send(view=buttonView())
        else:
            if embed is not None:
                await ctx.reply(embed=embed, ephemeral=isEph)
            if hasMessage:
                await ctx.reply(msg, ephemeral=isEph)
            if buttonView is not None:
                await ctx.reply(view=buttonView(), ephemeral=isEph)
    if channel is not None:
        if embed is not None:
            await channel.send(embed=embed)
        if hasMessage:
            await channel.send(msg)
        if buttonView is not None:
            await channel.send(view=buttonView())
    if DMUser is not None:
        if embed is not None:
            await DMUser.send(embed=embed)
        if hasMessage:
            await DMUser.send(msg)
        if buttonView is not None:
            await DMUser.send(view=buttonView())


async def sendResponse(mainData: dict, DMUser: discord.User | None, interaction: discord.Interaction | None = None,
                       ctx: discord.ext.commands.context.Context | None = None) -> tuple:
    if len(mainData) == 0:
        return "No data given", ""

    eph = utils.configManager.getEphPlaceholder()
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

        try:
            if (len(messages) == 0 and embed is None and len(DMMessages) == 0 and len(DMEmbeds) == 0 and
                    len(DMButtons) == 0 and len(channelEmbeds) == 0 and len(channelMessages) == 0 and
                    len(channelButtons) == 0):
                return "No data given", str(data.get("execution_path", ""))

            if interaction is None and ctx is None and channel is None:
                return (f"Expected valid text channel when there is no interaction! for message {messageName}",
                        str(data.get("execution_path", "")))

            await handleMessageResponse(None, embed, None, None, None,
                                        isEmbedEph(embed, eph), interaction=interaction, ctx=ctx)

            for msg in messages:
                await handleMessageResponse(msg, None, None, None, None,
                                            isMsgEph(msg, eph), interaction=interaction, ctx=ctx)

            if channel is not None:
                for channelMessage in channelMessages:
                    await handleMessageResponse(channelMessage, None, None, channel, None,
                                                isMsgEph(channelMessage, eph), interaction=interaction, ctx=ctx)
                for channelEmbed in channelEmbeds:
                    await handleMessageResponse(None, channelEmbed, None, channel, None,
                                                isEmbedEph(channelEmbed, eph), interaction=interaction, ctx=ctx)
                for channelButton in channelButtons:
                    await handleMessageResponse(None, None, buttonView, channel, None,
                                                buttonView.is_active_placeholder, interaction=interaction, ctx=ctx)
                    await channel.send(view=channelButton())

            if DMUser is not None:
                for DM in DMMessages:
                    await handleMessageResponse(DM, None, None, None, DMUser,
                                                isMsgEph(DM, eph), interaction=interaction, ctx=ctx)
                for DMEmbed in DMEmbeds:
                    await handleMessageResponse(None, DMEmbed, None, None, DMUser,
                                                isEmbedEph(DMEmbed, eph), interaction=interaction, ctx=ctx)
                for DMButton in DMButtons:
                    await handleMessageResponse(None, None, DMButton, None, DMUser,
                                                buttonView.is_active_placeholder, interaction=interaction, ctx=ctx)

            if buttonView is not None:
                await handleMessageResponse(None, None, buttonView, None, None,
                                            buttonView.is_active_placeholder, interaction=interaction, ctx=ctx)
        except Exception as e:
            return e, str(data.get("execution_path", ""))
    return None, ""


async def MainBuild(bot: commands.Bot, commandName: str, executionPath: str, placeholders: dict,
                    allMessages: list | None = None, interaction: discord.Interaction | None = None,
                    ctx: discord.ext.commands.context.Context | None = None):
    placeholders = placeholders_utils.addDefaultPlaceholder(placeholders, interaction=interaction, ctx=ctx)
    multiMessage = dict()
    if allMessages is None:
        commandMessages = utils.configManager.getCommandData(commandName).get("message_names", [])
        if not isinstance(commandMessages, list):
            raise Exception("`message_names` is not a list! Expected a list.")
    else:
        commandMessages = allMessages.copy()
    for msg in commandMessages:
        execPath = executionPath + ":" + msg
        multiMessage = await __handleOneMessage(bot, commandName, ctx, execPath, interaction, msg, multiMessage,
                                                placeholders, None)

    return multiMessage


async def __handleOneMessage(bot, commandName, ctx, executionPath, interaction, msg, multiMessage, placeholders,
                             error) -> dict:
    (DM, DMEmbeds, DMButtons) = await buildDMData(bot, commandName, msg, executionPath, placeholders,
                                                  interaction=interaction, ctx=ctx)
    (builtChannelEmbeds, builtChannelMessages, channel, builtChannelButtons) = (
        await buildChannelData(bot, commandName, msg, placeholders, executionPath, error, interaction=interaction,
                               ctx=ctx))
    multiMessage[msg] = {"messages": buildMessageData(commandName, msg, placeholders),
                         "embed": await buildEmbed(bot, commandName, msg, executionPath, placeholders, error,
                                                   interaction=interaction, ctx=ctx),
                         "dm_messages": DM,
                         "dm_embeds": DMEmbeds,
                         "dm_buttons": DMButtons,
                         "channel_embeds": builtChannelEmbeds,
                         "channel_messages": builtChannelMessages,
                         "channel_buttons": builtChannelButtons,
                         "channel": channel,
                         "button": buttons.buildButtonData(bot, msg, placeholders),
                         "execution_path": executionPath}
    return multiMessage


async def isCommandRestricted(bot: commands.Bot, commandName: str, executionPath: str,
                              interaction: discord.Interaction | None = None,
                              ctx: discord.ext.commands.context.Context | None = None) -> bool:
    if interaction is None and ctx is None:
        return False
    else:
        reason, actionList = await utils.isUserRestricted(bot, commandName, executionPath, interaction=interaction,
                                                          ctx=ctx)
        if len(reason.replace(" ", "")) > 0:
            actionData: dict = dict()
            for action in actionList:
                actionData[action] = utils.configManager.getActionData(action).copy()
            await actions.handleAllActions(bot, actionData, interaction=interaction, ctx=ctx,
                                           placeholders={utils.configManager.getReasonPlaceholder(): reason})
            return True
        return False


async def buildChannelData(bot: commands.Bot, commandName: str, message: str, placeholders: dict, executionPath: str,
                           error, interaction: discord.Interaction | None = None,
                           ctx: discord.ext.commands.context.Context | None = None) -> tuple:
    if bot is None and interaction is None and ctx is None:
        raise Exception("Code error!")
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
        return [], [], None, []

    if isinstance(channel, discord.TextChannel):
        return builtChannelEmbeds, builtChannelMessages, channel, builtChannelButtons

    if error is None:
        raise Exception("Text channel expected")
    else:
        return [], [], None, []


def buildMessageData(commandName: str, msg: str, placeholders: dict) -> list:
    message: list = utils.configManager.getCommandMessages(commandName, msg).copy()
    if len(message) > 0:
        for i in range(len(message)):
            message[i] = placeholders_utils.usePlaceholders(message[i], placeholders)
    return message


async def buildDMData(bot: commands.Bot, command: str, msg: str, executionPath: str, placeholders: dict,
                      interaction: discord.Interaction | None = None,
                      ctx: discord.ext.commands.context.Context | None = None) -> tuple:
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


async def MainBuildError(bot: commands.Bot, commandName: str, executionPath: str, error,
                         placeholders: dict, interaction: discord.Interaction = None,
                         ctx: discord.ext.commands.context.Context | None = None) -> dict:
    if len(executionPath.replace(" ", "")) > 0:
        if ":" not in executionPath and "/" not in executionPath:
            executionPath += ":error"
        return await __handleOneMessage(bot, commandName, ctx, executionPath, interaction, executionPath,
                                        dict(), placeholders, error)
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
                embed.title = placeholders_utils.usePlaceholders(value, placeholders)
            elif key == utils.configManager.getEmbedAuthorName():
                embed.author.name = placeholders_utils.usePlaceholders(value, placeholders)
            elif key == utils.configManager.getEmbedAuthorUrl():
                embed.author.url = placeholders_utils.usePlaceholders(value, placeholders)
            elif key == utils.configManager.getEmbedAuthorIconUrl():
                embed.author.icon_url = placeholders_utils.usePlaceholders(value, placeholders)
            elif key == utils.configManager.getEmbedFooter():
                embed.footer.text = placeholders_utils.usePlaceholders(value, placeholders)
            elif key == utils.configManager.getEmbedFooterIconUrl():
                embed.footer.icon_url = placeholders_utils.usePlaceholders(value, placeholders)
            elif key == utils.configManager.getEmbedImageUrl():
                embed.image.url = placeholders_utils.usePlaceholders(value, placeholders)
            elif key == utils.configManager.getEmbedDescription():
                embed.description = placeholders_utils.usePlaceholders(value, placeholders)
            elif key == utils.configManager.getEmbedColor():
                embed.colour = utils.getColour(placeholders_utils.usePlaceholders(value, placeholders))
            elif key == utils.configManager.getEmbedFields():
                notinlinePlaceholder = utils.configManager.getNotInLinePlaceholder()
                if not isinstance(value, dict):
                    raise Exception("Embed " + message_key +
                                    " needs fields as map: Example (" + notinlinePlaceholder +
                                    " placeholder is optional): " +
                                    "'" + utils.configManager.getEmbedFields() + "': {'FieldName': 'FieldValue " +
                                    notinlinePlaceholder + "'}")
                for k, v in data.get(utils.configManager.getEmbedFields()).items():
                    v = placeholders_utils.usePlaceholders(v, placeholders)
                    k = placeholders_utils.usePlaceholders(k, placeholders)
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


async def handleMessage(bot: commands.Bot, commandName: str, executionPath: str, allMessages: list | None = None,
                        singleMessage: str | None = None, placeholders: dict = dict(),
                        DMUser: discord.User | None = None,
                        interaction: discord.Interaction | None = None,
                        ctx: discord.ext.commands.context.Context | None = None) -> dict:
    statusData: dict = {"message": False, "error": False, "error_actions": False}
    execPath = ""
    try:
        if singleMessage is not None:
            mainData: dict = await __handleOneMessage(bot, commandName, ctx, executionPath, interaction, singleMessage,
                                                      {}, placeholders, None)
        else:
            mainData: dict = await MainBuild(bot, commandName, executionPath=executionPath, placeholders=placeholders,
                                             allMessages=allMessages, interaction=interaction, ctx=ctx)
        error, execPath = await sendResponse(mainData, DMUser=DMUser, interaction=interaction, ctx=ctx)
        if error is not None:
            raise Exception(error)
    except Exception as e:
        statusData["message"] = False
        if execPath == "":
            execPath = executionPath
        statusData.update(await handleError(bot, commandName, execPath, e, placeholders=placeholders,
                                            interaction=interaction, ctx=ctx))
    else:
        statusData["message"] = True
    return statusData


async def handleError(bot: commands.Bot, commandName: str, executionPath: str, error,
                      placeholders: dict = dict(),
                      interaction: discord.Interaction | None = None,
                      ctx: discord.ext.commands.context.Context | None = None) -> dict:
    errorData: dict = {"error": False, "error_actions": False}
    if error is not None:
        placeholders[utils.configManager.getErrorPlaceholder()] = error
        placeholders[utils.configManager.getErrorPathPlaceholder()] = executionPath
        try:
            exError, executionPath2 = await sendResponse(await MainBuildError(bot, commandName, executionPath, error,
                                                                              placeholders=placeholders,
                                                                              interaction=interaction,
                                                                              ctx=ctx), DMUser=None, ctx=ctx,
                                                         interaction=interaction)
            if exError is not None:
                raise Exception(exError)
        except Exception as ex:
            if utils.configManager.isPrintError():
                print("original error:", error, "follow up error:", ex)
            errorData["error"] = False
        else:
            errorData["error"] = True
            await actions.handleErrorActions(bot, executionPath, interaction=interaction, ctx=ctx,
                                             placeholders=placeholders)
    return errorData


async def handleInvalidMember(bot: commands.Bot, command: str, executionPath: str, error,
                              interaction: discord.Interaction | None = None,
                              ctx: discord.ext.commands.context.Context | None = None) -> dict:
    return await handleError(bot, command, executionPath, error,
                             placeholders={
                                 utils.configManager.getInvalidUsernamePlaceholder(): error},
                             interaction=interaction, ctx=ctx)


async def handleInvalidRole(bot: commands.Bot, command: str, executionPath: str, error,
                            interaction: discord.Interaction | None = None,
                            ctx: discord.ext.commands.context.Context | None = None) -> dict:
    return await handleError(bot, command, executionPath, error,
                             placeholders={utils.configManager.getInvalidUsernamePlaceholder(): error},
                             interaction=interaction, ctx=ctx)


async def handleInvalidArg(bot: commands.Bot, command: str, executionPath: str, error,
                           interaction: discord.Interaction | None = None,
                           ctx: discord.ext.commands.context.Context | None = None) -> dict:
    return await handleError(bot, command, executionPath, error,
                             placeholders={utils.configManager.getInvalidArgumentPlaceholder(): error},
                             interaction=interaction, ctx=ctx)


async def handleInvalidChannels(bot: commands.Bot, command: str, executionPath: str, error,
                                interaction: discord.Interaction | None = None,
                                ctx: discord.ext.commands.context.Context | None = None) -> dict:
    return await handleError(bot, command, executionPath, error,
                             placeholders={utils.configManager.getInvalidChannelPlaceholder(): error},
                             interaction=interaction, ctx=ctx)
