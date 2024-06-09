from cogs.ext.imports import *

async def handleActionMessages(bot: commands.Bot, messages_names: list, commandName: str,
                               executionPath: str, placeholders: dict, interaction: discord.Interaction | None = None,
                               ctx: discord.ext.commands.context.Context | None = None):
    # action = name of the action
    # doing = messages
    placeholders[utils.configManager.getActionPathPlaceholder()] = executionPath
    for msg in messages_names:
        messageData: dict = await messages.handleMessage(bot, commandName, executionPath,
                                                         singleMessage=msg, placeholders=placeholders,
                                                         interaction=interaction, ctx=ctx)
        if not messageData["message"]:
            return


async def handleCogCommandExecution(bot: commands.Bot, cog: commands.Cog,
                                    command: Any, finalArgs: list,
                                    executionPath: str, placeholders: dict,
                                    interaction: discord.Interaction | None = None,
                                    ctx: discord.ext.commands.context.Context | None = None):
    for co in cog.get_app_commands():
        if co.name == command.name:
            try:
                await command.callback(cog, interaction if interaction is not None else ctx, *finalArgs)
            except Exception as e:
                await messages.handleError(bot, command.name, executionPath, e, placeholders=placeholders,
                                           ctx=ctx, interaction=interaction)


async def handleActionCommands(bot: commands.Bot, commandsData: list, executedPath: str,
                               placeholders: dict, commandName: str, interaction: discord.Interaction | None = None,
                               ctx: discord.ext.commands.context.Context | None = None):
    for singleCommandData in commandsData:
        if not isinstance(singleCommandData, dict):
            await messages.handleError(bot, commandName, executedPath,
                                       "Expected command data to be map. Example: {'command': ['argument']}. But got type " +
                                       f"{type(singleCommandData)}",
                                       placeholders=placeholders, interaction=interaction)
            break
        command = str(singleCommandData.get("command"))
        isCommandApp = str(singleCommandData.get("type", "")) == "app"
        comm = bot.tree.get_command(command) if isCommandApp else bot.get_command(command)
        if comm is not None:
            args = singleCommandData.get("args", [])
            if not isinstance(args, list):
                args = []

            for placeholder in placeholders.keys():
                if placeholder in args:
                    ind = args.index(placeholder)
                    args.pop(ind)
                    args.insert(ind, placeholders.get(placeholder))

            executed = False
            for name, file_name in utils.configManager.getCogData().items():
                cog: commands.Cog = bot.get_cog(name)
                for cogCommand in cog.get_app_commands() if isCommandApp else cog.get_commands():
                    if cogCommand.name == comm.name:
                        try:
                            await bot.load_extension(f"cogs.{file_name}")
                        except commands.ExtensionAlreadyLoaded:
                            await handleCogCommandExecution(bot, cog, comm, args, executedPath, placeholders,
                                                            interaction=interaction, ctx=ctx)
                            executed = True
                        else:
                            await bot.unload_extension(f"cogs.{file_name}")
                        break
                if executed:
                    break


def startBackgroundTask(taskArgs: dict, function = None, functionArgs = None):
    taskArgs["function"] = function
    taskArgs["functionArgs"] = functionArgs
    async def wait(tasks: dict):
        try:
            await asyncio.sleep(tasks["duration"])
            await tasks["function"](*tasks["functionArgs"])
        except Exception as e:
            await messages.handleError(tasks["bot"], tasks["commandName"], tasks["executedPath"], e,
                                       placeholders=tasks["placeholders"], interaction=tasks["interaction"],
                                       ctx=tasks["ctx"])

    threading.Thread(target=utils.separateThread, args=(asyncio.get_running_loop(), wait, taskArgs),
                     daemon=True).start()


def checkIFAnyValuableData(listData: list) -> str:
    for listDataItem in listData:
        if not isinstance(listDataItem, dict):
            return "The provided data is incorrect. Expected map! Example: {'role_id': ..., 'role_name':...}"
    return ""


async def actionBanUsers(members: List[discord.Member], reason: str):
    for member in members:
        await utils.banUser(member, reason=reason)


async def actionUnbanUsers(members: List[discord.Member], reason: str):
    for member in members:
        await utils.unbanUser(member, reason=reason)


async def actionRemoveUserRoles(roles: Dict[discord.Role, List[discord.Member]], reason: str):
    for role, members in roles.items():
        for member in members:
            await utils.removeRole(member, role, reason=reason)


async def actionAddUserRoles(roles: Dict[discord.Role, List[discord.Member]], reason: str):
    for role, members in roles.items():
        for member in members:
            await utils.addRole(member, role, reason=reason)


async def actionRemoveUserTimeout(timeoutMembers: List[discord.Member], reason: str):
    for mem in timeoutMembers:
        await utils.removeUserTimeout(mem, reason=reason)


async def actionRemoveUserDeafen(members: List[discord.Member], reason: str):
    for mem in members:
        await utils.userDeafen(mem, False, reason=reason)


async def actionUserDeafen(members: List[discord.Member], reason: str):
    for mem in members:
        await utils.userDeafen(mem, True, reason=reason)


async def actionRemoveUserMute(members: List[discord.Member], reason: str):
    for mem in members:
        await utils.userMute(mem, False, reason=reason)


async def actionUserMute(members: List[discord.Member], reason: str):
    for mem in members:
        await utils.userMute(mem, True, reason=reason)


async def actionCreateRole(roles: List[discord.Role], reason: str, give_back_roles_to_users: bool,
                           give_back_reason: str, guild: discord.Guild):
    for roleToCreate in roles:
        roleData: dict = utils.getRoleData(roleToCreate)
        roleData["reason"] = reason
        if not give_back_roles_to_users:
            roleData.pop("users")
        try:
            role = await utils.createRole(roleData, guild)
        except Exception as e:
            raise Exception(f"Error {e} Couldn't create a role with this data: {roleData}")
        if "users" not in roleData.keys() or len(roleData.get("users", [])) == 0:
            continue
        for userId in roleData.get("users", []):
            member: discord.Member | None = utils.getMemberGuild(guild, userId)
            if member is None:
                raise Exception(f"Couldn't find member with ID {userId} in {guild.name} : {guild.id} guild")
            await utils.addRole(member, role, reason=give_back_reason)


async def actionRoleEdit(roles: Dict[discord.Role, Dict], reason: str):
    for editedRole, prevData in roles.items():
        prevData["reason"] = reason
        prevData["new_name"] = prevData.pop("name")
        try:
            await utils.editRole(prevData, editedRole)
        except Exception as e:
            raise Exception(f"Couldn't edit back role {editedRole.name} : {editedRole.id} for reason {reason} " +
                            f"for guild {editedRole.guild.name} : {editedRole.guild.id}. Error {e}")


async def actionCategoryCreate(categories: List[discord.CategoryChannel], reason: str, guild: discord.Guild):
    for categories in categories:
        catData: dict = utils.getCategoryData(categories)
        catData["reason"] = reason
        await utils.createCategory(catData, guild)


async def actionCategoryEdit(categories: Dict[discord.CategoryChannel, Dict], reason: str):
    for category, prevData in categories.items():
        prevData["reason"] = reason
        prevData["new_name"] = prevData.pop("name")
        await utils.editCategory(category, prevData)


async def actionChannelDelete(channels: list, reason: str):
    for channel in channels:
        await utils.deleteChannel(channel, reason)


async def actionChannelCreate(channels: List[discord.abc.GuildChannel], reason: str):
    for channel in channels:
        data: dict = utils.getChannelData(channel)
        data["reason"] = reason
        await utils.createChannel(data, channel.guild)


async def actionChannelEdit(channels: Dict[discord.CategoryChannel, Dict], reason: str):
    for channel, prevData in channels.items():
        prevData["reason"] = reason
        prevData["new_name"] = prevData.pop("name")
        await utils.editChannel(prevData, channel)


async def actionCreateEmojis(emojis: List[discord.Emoji], reason: str):
    for emoji in emojis:
        data: dict = utils.getEmojiData(emoji)
        data["reason"] = reason
        await utils.createEmoji(data, emoji.guild)


async def actionEditEmojis(emojis: Dict[discord.Emoji, Dict], reason: str):
    for emoji, prevData in emojis.items():
        prevData["reason"] = reason
        prevData["new_name"] = prevData.pop("name")
        await utils.editEmoji(prevData, emoji)


async def handleUser(userData: dict, bot: commands.Bot, commandName: str,
                     executedPath: str, placeholders: dict, interaction: discord.Interaction | None = None,
                     ctx: discord.ext.commands.context.Context | None = None):
    for userDo in userData.keys():
        userDoDataList: list = userData.get(userDo, [])
        if not isinstance(userDoDataList, list):
            userDoDataList = [userDoDataList] if isinstance(userDoDataList, dict) else []
        elif len(userDoDataList) == 0:
            await messages.handleError(bot, commandName, executedPath,
                                       "Expected a map! Example: {'interact_both': False, 'user_id': ...}",
                                       placeholders=placeholders, interaction=interaction, ctx=ctx)
            break

        checkReason = checkIFAnyValuableData(userDoDataList)
        if len(checkReason) > 0:
            await messages.handleError(bot, commandName, executedPath, checkReason,
                                       placeholders=placeholders, interaction=interaction, ctx=ctx)
            break
        user = interaction.user if interaction is not None else ctx.author
        defaultArguments = {"bot": bot, "interaction": interaction, "duration": -1, "commandName": commandName,
                            "executedPath": executedPath, "ctx": ctx}
        if userDo not in ["ban", "unban", "kick", "role_add", "role_remove",
                          "timeout", "deafen", "deafen_remove", "mute", "mute_remove"]:
            continue

        executedPath = await handleExecutionPathFormat(executedPath, userDo)

        guild = interaction.guild if interaction is not None else ctx.guild
        if userDo == "ban":
            for i in range(len(userDoDataList)):
                userDoData = userDoDataList[i]
                reason = str(userDoData.get("reason", ""))

                usersBanned: list = []
                if bool(userDoData.get("interact_both", True)):
                    try:
                        await utils.banUser(user, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath, {"error": e,
                                 "message": f"Couldn't ban user {user.name} : {user.id} for reason {reason}"},
                                                   placeholders=placeholders, interaction=interaction, ctx=ctx)
                    else:
                        usersBanned.append(user)

                for userToBan in utils.getMembers(userDoData, guild):
                    try:
                        await utils.banUser(userToBan, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath, {"error": e,
                                                                                    "message": f"Couldn't ban user {userToBan.name} : {userToBan.id} for reason {reason}"},
                                                   placeholders=placeholders, interaction=interaction, ctx=ctx)
                        break
                    else:
                        usersBanned.append(userToBan)

                duration: int = int(userDoData.get("duration", -1))
                if duration > 0 and len(usersBanned) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(defaultArguments, function=actionUnbanUsers,
                                        functionArgs=[usersBanned, str(userDoData.get("unban_reason", ""))])
        elif userDo == "unban":
            for i in range(len(userDoDataList)):
                userDoData = userDoDataList[i]
                duration: int = int(userDoData.get("duration", -1))
                reason = str(userDoData.get("reason", ""))

                usersUnbanned: list = []
                for resUser in utils.getBannedMembers(userDoData, guild):
                    try:
                        await utils.unbanUser(resUser, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"error": e,
                                                    "message":
                                                        f"Couldn't unban user "+
                                                        f"{resUser.name} : {resUser.id} for reason {reason}"},
                                                   placeholders=placeholders, interaction=interaction, ctx=ctx)
                        break
                    else:
                        usersUnbanned.append(user)

                if duration > 0 and len(usersUnbanned) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(defaultArguments, function=actionBanUsers,
                                        functionArgs=[usersUnbanned, str(userDoData.get("unban_reason", ""))])
        elif userDo == "kick":
            for i in range(len(userDoDataList)):
                userDoData = userDoDataList[i]
                users: list = utils.getMembers(userDoData, guild)
                reason = str(userDoData.get("reason", ""))
                if bool(userDoData.get("interact_both", True)):
                    try:
                        await utils.kickUser(user, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"error": e,
                                                    "message":
                                                        f"Couldn't kick user {user.name} : {user.id} for reason {reason}"},
                                                   placeholders=placeholders, interaction=interaction, ctx=ctx)

                for resUser in users:
                    try:
                        await utils.kickUser(resUser, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"error": e,
                                                    "message":
                                                        f"Couldn't kick user {resUser.name} : {resUser.id} for reason {reason}"},
                                                   placeholders=placeholders, interaction=interaction, ctx=ctx)
                        break
        elif userDo == "role_add":
            for i in range(len(userDoDataList)):
                userDoData = userDoDataList[i]
                duration: int = int(userDoData.get("duration", -1))
                users: list = utils.getMembers(userDoData, guild)
                reason = str(userDoData.get("reason", ""))

                roleAdded: dict = dict()
                for role in utils.getRoles(userDoData, guild):
                    roleAdded[role] = []
                    if bool(userDoData.get("interact_both", True)):
                        try:
                            await utils.addRole(user, role, reason=reason)
                        except Exception as e:
                            await messages.handleError(bot, commandName, executedPath,
                                                       {"error": e, "message":
                    f"Couldn't add role {role.name} : {role.id} to user {user.name} : {user.id} for reason {reason}"},
                                                       placeholders=placeholders, interaction=interaction, ctx=ctx)
                        else:
                            roleAdded[role].append(user)

                    for resUser in users:
                        try:
                            await utils.addRole(resUser, role, reason=reason)
                        except Exception as e:
                            await messages.handleError(bot, commandName, executedPath,
                                                       {"error": e,
                                                        "message":
                                                            f"Couldn't add role {role.name} : {role.id} to user {resUser.name} : {resUser.id} for reason {reason}"},
                                                       placeholders=placeholders, interaction=interaction, ctx=ctx)
                            break
                        else:
                            roleAdded[role].append(resUser)
                hasData = False
                for itemK, itemV in roleAdded.items():
                    if len(itemV) > 0:
                        hasData = True
                        break
                if duration > 0 and hasData:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(defaultArguments, function=actionRemoveUserRoles,
                                        functionArgs=[roleAdded, str(userDoData.get("role_remove_reason", ""))])
        elif userDo == "role_remove":
            for i in range(len(userDoDataList)):
                userDoData = userDoDataList[i]
                duration: int = int(userDoData.get("duration", -1))
                users: list = utils.getMembers(userDoData, guild)
                reason = str(userDoData.get("reason", ""))

                roleRemoved: dict = dict()
                for role in utils.getRoles(userDoData, guild):
                    roleRemoved[role] = []
                    if bool(userDoData.get("interact_both", True)):
                        try:
                            await utils.removeRole(user, role, reason=reason)
                        except Exception as e:
                            await messages.handleError(bot, commandName, executedPath,
                                                       {"error": e, "message":
                                                           f"Couldn't remove role " +
                                                           f"{role.name} : {role.id} to user " +
                                                           f"{user.name} : {user.id} for reason {reason}"},
                                                       placeholders=placeholders, interaction=interaction, ctx=ctx)
                        else:
                            roleRemoved[role].append(user)
                    for resUser in users:
                        try:
                            await utils.removeRole(resUser, role, reason=reason)
                        except Exception as e:
                            await messages.handleError(bot, commandName, executedPath,
                                                       {"error": e, "message":
                                                           f"Couldn't remove role " +
                                                           f"{role.name} : {role.id} to user " +
                                                           f"{resUser.name} : {resUser.id} for reason {reason}"},
                                                       placeholders=placeholders, interaction=interaction, ctx=ctx)
                            break
                        else:
                            roleRemoved[role].append(resUser)
                hasData = False
                for itemK, itemV in roleRemoved.items():
                    if len(itemV) > 0:
                        hasData = True
                        break
                if duration > 0 and hasData:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(defaultArguments, function=actionAddUserRoles,
                                        functionArgs=[roleRemoved, str(userDoData.get("role_add_reason", ""))])
        elif userDo == "timeout":
            for i in range(len(userDoDataList)):
                userDoData = userDoDataList[i]
                duration: int = int(userDoData.get("duration", -1))
                reason = str(userDoData.get("reason", ""))
                if "until" not in userDoData.keys():
                    await messages.handleError(bot, commandName, executedPath,
                                               "Until data is invalid! Format expected: " +
                                               "YEAR-MOUNT-DAYTHOURS:MINS:SECONDS Like: 2024-06-09T04:12:52",
                                               placeholders=placeholders, interaction=interaction, ctx=ctx)
                    break
                else:
                    try:
                        until_datetime = datetime.strptime(str(userDoData.get("until")),
                                                           "YYYY-MM-DDTHH:MM:SS")
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"error": e, "message":
                                                       "Until data is invalid! Format expected: " +
                                                       "YEAR-MOUNT-DAYTHOURS:MINS:SECONDS Like: 2024-06-09T04:12:52"},
                                                   placeholders=placeholders, interaction=interaction, ctx=ctx)
                        break
                timeout_datetime = datetime.now() + timedelta(
                    days=until_datetime.year * 365 + until_datetime.month * 30 +
                         until_datetime.day, hours=until_datetime.hour,
                    minutes=until_datetime.minute, seconds=until_datetime.second)
                timeoutedMembers: list = []
                if bool(userDoData.get("interact_both", True)):
                    try:
                        await utils.timeoutUser(user, datetime.now().strptime, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"error": e, "message":
                                                       f"Couldn't timeout user {user.name} : {user.id} to date " +
                                                       f"{timeout_datetime}"},
                                                   placeholders=placeholders, interaction=interaction, ctx=ctx)

                    else:
                        timeoutedMembers.append(user)
                for resUser in utils.getMembers(userDoData, guild):
                    try:
                        await utils.timeoutUser(resUser, timeout_datetime, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"error": e, "message":
                                                       f"Couldn't timeout user " +
                                                       f"{resUser.name} : {resUser.id} to date {timeout_datetime}"},
                                                   placeholders=placeholders, interaction=interaction, ctx=ctx)
                        break
                    else:
                        timeoutedMembers.append(resUser)
                if duration > 0 and len(timeoutedMembers) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(defaultArguments, function=actionRemoveUserTimeout,
                                        functionArgs=[timeoutedMembers,
                                                      str(userDoData.get("timeout_remove_reason", ""))])
        elif userDo == "deafen":
            for i in range(len(userDoDataList)):
                userDoData = userDoDataList[i]
                duration: int = int(userDoData.get("duration", -1))
                reason = str(userDoData.get("reason", ""))

                deafenMembers: list = []
                if bool(userDoData.get("interact_both", True)):
                    try:
                        await utils.userDeafen(user, True, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"message":
                                                        f"Couldn't deafen user " +
                                                        f"{user.name} : {user.id} for reason {reason}",
                                                    "error": e},
                                                   placeholders=placeholders, interaction=interaction, ctx=ctx)
                    else:
                        deafenMembers.append(user)
                for resUser in utils.getMembers(userDoData, guild):
                    try:
                        await utils.userDeafen(resUser, True, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"message":
                                                        f"Couldn't deafen user " +
                                                        f"{resUser.name} : {resUser.id} for reason {reason}",
                                                    "error": e},
                                                   placeholders=placeholders, interaction=interaction, ctx=ctx)
                        break
                    else:
                        deafenMembers.append(resUser)

                if duration > 0 and len(deafenMembers) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(defaultArguments, function=actionRemoveUserDeafen,
                                        functionArgs=[deafenMembers, str(userDoData.get("deafen_remove_reason", ""))])
        elif userDo == "deafen_remove":
            for i in range(len(userDoDataList)):
                userDoData = userDoDataList[i]
                duration: int = int(userDoData.get("duration", -1))
                users: list = utils.getMembers(userDoData, guild)
                reason = str(userDoData.get("reason", ""))

                removeDeafenMembers: list = []
                if bool(userDoData.get("interact_both", True)):
                    try:
                        await utils.userDeafen(user, False, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"message":
                                                        f"Couldn't undeafen user " +
                                                        f"{user.name} : {user.id} for reason {reason}",
                                                    "error": e},
                                                   placeholders=placeholders, interaction=interaction, ctx=ctx)
                    else:
                        removeDeafenMembers.append(user)
                for resUser in users:
                    try:
                        await utils.userDeafen(resUser, False, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"error": e, "message":
                                                       f"Couldn't undeafen user " +
                                                       f"{resUser.name} : {resUser.id} for reason {reason}"},
                                                   placeholders=placeholders, interaction=interaction, ctx=ctx)
                        break
                    else:
                        removeDeafenMembers.append(resUser)

                if duration > 0 and len(removeDeafenMembers) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(defaultArguments, function=actionUserDeafen,
                                        functionArgs=[removeDeafenMembers, str(userDoData.get("deafen_reason", ""))])
        elif userDo == "mute":
            for i in range(len(userDoDataList)):
                userDoData = userDoDataList[i]
                duration: int = int(userDoData.get("duration", -1))
                users: list = utils.getMembers(userDoData, guild)
                reason = str(userDoData.get("reason", ""))
                removeMutedMembers: list = []

                if bool(userDoData.get("interact_both", True)):
                    try:
                        await utils.userMute(user, True, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"message":
                                                        f"Couldn't muted user " +
                                                        f"{user.name} : {user.id} for reason {reason}",
                                                    "error": e},
                                                   placeholders=placeholders, interaction=interaction, ctx=ctx)
                    else:
                        removeMutedMembers.append(user)
                for resUser in users:
                    try:
                        await utils.userMute(resUser, True, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"message":
                                                        f"Couldn't muted user " +
                                                        f"{resUser.name} : {resUser.id} for reason {reason}",
                                                    "error": e},
                                                   placeholders=placeholders, interaction=interaction, ctx=ctx)
                        break
                    else:
                        removeMutedMembers.append(resUser)

                if duration > 0 and len(removeMutedMembers) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(defaultArguments, function=actionRemoveUserMute,
                                        functionArgs=[removeMutedMembers,
                                                      str(userDoData.get("mute_remove_reason", ""))])
        elif userDo == "mute_remove":
            for i in range(len(userDoDataList)):
                userDoData = userDoDataList[i]
                duration: int = int(userDoData.get("duration", -1))
                users: list = utils.getMembers(userDoData, guild)
                reason = str(userDoData.get("reason", ""))
                removeMutedMembers: list = []
                if bool(userDoData.get("interact_both", True)):
                    try:
                        await utils.userMute(user, False, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"error": e,
                                                    "message": f"Couldn't unmute user " +
                                                               f"{user.name} : {user.id} for reason {reason}"},
                                                   placeholders=placeholders, interaction=interaction, ctx=ctx)
                    else:
                        removeMutedMembers.append(user)

                for resUser in users:
                    try:
                        await utils.userMute(resUser, False, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"error": e,
                                                    "message": f"Couldn't unmute user " +
                                                               f"{resUser.name} : {resUser.id} for reason {reason}"},
                                                   placeholders=placeholders, interaction=interaction, ctx=ctx)
                        break
                    else:
                        removeMutedMembers.append(resUser)

                if duration > 0 and len(removeMutedMembers) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(defaultArguments, function=actionUserMute,
                                        functionArgs=[removeMutedMembers, str(userDoData.get("mute_reason", ""))])


async def handleGuild(guildData: dict, bot: commands.Bot, commandName: str,
                      executedPath: str, placeholders: dict, interaction: discord.Interaction | None = None,
                      ctx: discord.ext.commands.context.Context | None = None):
    guild = interaction.guild if interaction is not None else ctx.guild
    defaultArguments = {"bot": bot, "interaction": interaction, "duration": -1, "commandName": commandName,
                        "executedPath": executedPath, "ctx": ctx}
    for guildToDo in guildData.keys():
        listData = guildData.get(guildToDo, [])
        if not isinstance(listData, list):
            listData = [listData] if isinstance(listData, dict) else []
        elif len(listData) == 0:
            await messages.handleError(bot, commandName, executedPath,
                                       "No data has been provided. Expected map! Example: " +
                                       "{'role_id': ..., 'role_name':...}",
                                       placeholders=placeholders, interaction=interaction, ctx=ctx)
            break

        checkReason = checkIFAnyValuableData(listData)
        if len(checkReason) > 0:
            await messages.handleError(bot, commandName, executedPath, checkReason, placeholders=placeholders,
                                       interaction=interaction, ctx=ctx)
            break

        if guildToDo not in ["role_create", "role_delete", "role_edit", "overview", "category_create",
                             "category_delete", "channel_create", "category_edit", "channel_delete", "channel_edit",
                             "emoji_create", "emoji_delete", "emoji_edit"]:
            continue

        executedPath = await handleExecutionPathFormat(executedPath, guildToDo)

        guild_id = guild.id
        guild_name = guild.name
        if guildToDo == "role_create":
            for i in range(len(listData)):
                rolesData: dict = listData[i]
                try:
                    role = await utils.createRole(rolesData, guild)
                except Exception as e:
                    await messages.handleError(bot, commandName, executedPath,
                                               {"error": e, "message":
                                                   f"Couldn't create role " +
                                                   f"{rolesData.get('name')} for reason {rolesData.get('reason')} "
                                                   f"in guild {guild_name} : {guild_id}"},
                                               placeholders=placeholders, interaction=interaction, ctx=ctx)
                    break
                duration: int = int(rolesData.get("duration", -1))
                if duration > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(defaultArguments, function=utils.deleteRole,
                                        functionArgs=[role, str(rolesData.get("role_delete_reason", ""))])
        elif guildToDo == "role_delete":
            for i in range(len(listData)):
                rolesData = listData[i]
                roles: list = []
                for selectedRole in utils.getRoles(rolesData, guild):
                    try:
                        await utils.deleteRole(selectedRole, reason=rolesData.get("reason", ""))
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"error": e, "message":
                                                       f"Couldn't delete role {selectedRole.name} : {selectedRole.id} " +
                                                       f"for reason {rolesData.get('reason')} in guild " +
                                                       f"{guild_name} : {guild_id}"},
                                                   placeholders=placeholders, interaction=interaction, ctx=ctx)
                        break
                    else:
                        roles.append(selectedRole)
                duration: int = int(rolesData.get("duration", -1))
                if duration > 0 and len(roles) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(defaultArguments, function=actionCreateRole,
                                        functionArgs=[roles, str(rolesData.get("role_create_reason", "")),
                                                      bool(rolesData.get("give_back_roles_to_users", False)),
                                                      str(rolesData.get("give_back_reason", "")), guild])
        elif guildToDo == "role_edit":
            for i in range(len(listData)):
                rolesData = listData[i]
                edited: Dict[discord.Role, Dict] = dict()
                for role in utils.getRoles(rolesData, guild):
                    prevStatus: dict = utils.getRoleData(role)
                    try:
                        await utils.editRole(rolesData, role)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"error": e, "message":
                                                       f"Couldn't edit role {role.name} : {role.id} " +
                                                       f"for reason {rolesData.get('reason')} " +
                                                       f"in guild {guild_name} : {guild_id}"},
                                                   placeholders=placeholders, interaction=interaction, ctx=ctx)
                        break
                    else:
                        edited[role] = prevStatus
                duration: int = int(rolesData.get("duration", -1))
                if duration > 0 and len(edited) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(defaultArguments, function=actionRoleEdit,
                                        functionArgs=[edited, str(rolesData.get("role_edit_reason", ""))])
        elif guildToDo == "overview":
            for i in range(len(listData)):
                overviewData = listData[i]
                fullPrevData: dict = utils.getGuildData(guild)
                reason = str(overviewData.get("reason", ""))
                try:
                    await utils.editGuild(overviewData, guild, reason)
                except Exception as e:
                    await messages.handleError(bot, commandName, executedPath,
                                               {"error": e, "message":
                                                   f"Couldn't edit guild {guild_name} : {guild_id} for reason {reason}"
                                                },
                                               placeholders=placeholders, interaction=interaction, ctx=ctx)
                    continue

                prevData: dict = dict()
                for key in overviewData.keys():
                    if key not in fullPrevData.keys():
                        continue
                    prevData[key] = fullPrevData.get(key)
                duration: int = int(overviewData.get("duration", -1))
                if duration > 0 and len(prevData) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(defaultArguments, function=utils.editGuild,
                                        functionArgs=[prevData, guild, str(overviewData.get("guild_edit_reason", ""))])
        elif guildToDo == "category_create":
            for i in range(len(listData)):
                categoryData = listData[i]
                try:
                    category: discord.CategoryChannel = await utils.createCategory(categoryData, guild)
                except Exception as e:
                    await messages.handleError(bot, commandName, executedPath,
                                               {"error": e, "message":
                                                   f"Couldn't create category {categoryData.get('name')}"
                                                   f" for reason {categoryData.get('reason')} " +
                                                   f"in guild {guild_name} : {guild_id}"},
                                               placeholders=placeholders, interaction=interaction, ctx=ctx)
                    continue
                duration: int = int(categoryData.get("duration", -1))
                if duration > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(defaultArguments, function=utils.deleteCategory,
                                        functionArgs=[category, str(categoryData.get("category_delete_reason", ""))])
        elif guildToDo == "category_delete":
            for i in range(len(listData)):
                categoryData = listData[i]
                deletedCategories: List[discord.CategoryChannel] = []
                reason = str(categoryData.get("reason", ""))
                for category in utils.getCategories(categoryData, guild):
                    if category is None:
                        continue
                    try:
                        await utils.deleteCategory(category, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"error": e,
                                                    "message": f"Couldn't delete category {categoryData.get('name')}"
                                                               f" for reason {reason} " +
                                                               f"in guild {guild_name} : {guild_id}"},
                                                   placeholders=placeholders, interaction=interaction, ctx=ctx)
                        break
                    else:
                        deletedCategories.append(category)

                duration: int = int(categoryData.get("duration", -1))
                if duration > 0 and len(deletedCategories) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(defaultArguments, function=actionCategoryCreate,
                                        functionArgs=[deletedCategories,
                                                      str(categoryData.get("category_delete_reason", "")), guild])
        elif guildToDo == "category_edit":
            for i in range(len(listData)):
                categoryData = listData[i]
                editedCategories: Dict[discord.CategoryChannel, Dict] = dict()
                for category in utils.getCategories(categoryData, guild):
                    if category is None:
                        continue
                    categoryPrevData: dict = utils.getCategoryData(category)
                    try:
                        await utils.editCategory(category, categoryData)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"error": e, "message":
                                                       f"Couldn't edit category {categoryData.get('name')}"
                                                       f" for reason {categoryData.get('reason')} " +
                                                       f"in guild {guild_name} : {guild_id}"},
                                                   placeholders=placeholders, interaction=interaction, ctx=ctx)
                        break
                    else:
                        editedCategories[category] = categoryPrevData

                duration: int = int(categoryData.get("duration", -1))
                if duration > 0 and len(editedCategories) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(defaultArguments, function=actionCategoryEdit,
                                        functionArgs=[editedCategories,
                                                      str(categoryData.get("category_edit_reason", ""))])
        elif guildToDo == "channel_create":
            for i in range(len(listData)):
                channelData = listData[i]
                try:
                    channels: List[discord.abc.GuildChannel] = await utils.createChannel(channelData, guild)
                except Exception as e:
                    await messages.handleError(bot, commandName, executedPath,
                                               {"error": e, "message":
                                                   f"Couldn't create channel {channelData.get('name')}"
                                                   f" for reason {channelData.get('reason')} " +
                                                   f"in guild {guild_name} : {guild_id}"},
                                               placeholders=placeholders, interaction=interaction, ctx=ctx)
                    continue

                duration: int = int(channelData.get("duration", -1))
                if duration > 0 and len(channels) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(defaultArguments, function=actionChannelDelete,
                                        functionArgs=[channels,
                                                      str(channelData.get("channel_delete_reason", ""))])
        elif guildToDo == "channel_delete":
            for i in range(len(listData)):
                channelData = listData[i]
                reason = str(channelData.get("reason", ""))
                deletedChannels: List[discord.abc.GuildChannel] = []
                for channel in utils.getChannels(channelData, guild):
                    try:
                        await utils.deleteChannel(channel, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"error": e, "message":
                                                       f"Couldn't delete channel {channelData.get('name')}"
                                                       f" for reason {reason} " +
                                                       f"in guild {guild_name} : {guild_id}"},
                                                   placeholders=placeholders, interaction=interaction, ctx=ctx)
                        break
                    else:
                        deletedChannels.append(channel)
                duration: int = int(channelData.get("duration", -1))
                if duration > 0 and len(deletedChannels) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(defaultArguments, function=actionChannelCreate,
                                        functionArgs=[deletedChannels,
                                                      str(channelData.get("channel_create_reason", ""))])
        elif guildToDo == "channel_edit":
            for i in range(len(listData)):
                channelData = listData[i]
                editedChannels: Dict[discord.abc.GuildChannel, Dict] = dict()
                for channel in utils.getChannels(channelData, guild):
                    if channel is None:
                        continue
                    channelPrevData: dict = utils.getChannelData(channel)
                    try:
                        await utils.editChannel(channelData, channel)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"error": e, "message":
                                                       f"Couldn't edit channel {channelData.get('name')}"
                                                       f" for reason {channelData.get('reason')} " +
                                                       f"in guild {guild_name} : {guild_id}"},
                                                   placeholders=placeholders, interaction=interaction, ctx=ctx)
                        break
                    else:
                        editedChannels[channel] = channelPrevData

                duration: int = int(channelData.get("duration", -1))
                if duration > 0 and len(editedChannels) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(defaultArguments, function=actionChannelEdit,
                                        functionArgs=[editedChannels,
                                                      str(channelData.get("channel_edit_reason", ""))])
        elif guildToDo == "emoji_create":
            for i in range(len(listData)):
                emojiData = listData[i]
                try:
                    emoji = await utils.createEmoji(emojiData, guild)
                except Exception as e:
                    await messages.handleError(bot, commandName, executedPath,
                                               {"error": e, "message":
                                                   f"Couldn't create emoji {emojiData.get('name')}"
                                                   f" for reason {emojiData.get('reason')} " +
                                                   f"in guild {guild_name} : {guild_id}"},
                                               placeholders=placeholders, interaction=interaction, ctx=ctx)
                    continue
                duration: int = int(emojiData.get("duration", -1))
                if duration > 0 and len(emojiData) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(defaultArguments, function=utils.deleteEmoji,
                                        functionArgs=[emoji, str(emojiData.get("emoji_delete_reason", ""))])
        elif guildToDo == "emoji_delete":
            for i in range(len(listData)):
                emojiData = listData[i]
                deletedEmojis: List[discord.Emoji] = []
                reason = str(emojiData.get("reason", ""))
                emojis = await utils.getEmojis(emojiData, guild)
                for emoji in emojis:
                    try:
                        await utils.deleteEmoji(emoji, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"error": e, "message":
                                                       f"Couldn't delete emoji {emojiData.get('name')}"
                                                       f" for reason {emojiData.get('reason')} " +
                                                       f"in guild {guild_name} : {guild_id}"},
                                                   placeholders=placeholders, interaction=interaction, ctx=ctx)
                        break
                    else:
                        deletedEmojis.append(emoji)
                duration: int = int(emojiData.get("duration", -1))
                if duration > 0 and len(emojiData) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(defaultArguments, function=actionCreateEmojis,
                                        functionArgs=[deletedEmojis, str(emojiData.get("emoji_create_reason", ""))])
        elif guildToDo == "emoji_edit":
            for i in range(len(listData)):
                emojiData = listData[i]
                editedEmojis: Dict[discord.Emoji, Dict] = dict()
                emojis = await utils.getEmojis(emojiData, guild)
                for emoji in emojis:
                    prevData = utils.getEmojiData(emoji)
                    try:
                        await utils.editEmoji(editedEmojis, emoji)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"error": e, "message":
                                                       f"Couldn't edit emoji {emoji.name}"
                                                       f" for reason {emojiData.get('reason')} " +
                                                       f"in guild {guild_name} : {guild_id}"},
                                                   placeholders=placeholders, interaction=interaction, ctx=ctx)
                        break
                    else:
                        editedEmojis[emoji] = prevData
                duration: int = int(emojiData.get("duration", -1))
                if duration > 0 and len(emojiData) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(defaultArguments, function=actionCreateEmojis,
                                        functionArgs=[actionEditEmojis, str(emojiData.get("emoji_edit_reason", ""))])


async def handleExecutionPathFormat(executedPath, guildToDo):
    if guildToDo not in executedPath:
        if executedPath.count("/") > 1:
            pathSpl = executedPath.split("/")
            for i in range(len(pathSpl) - 1):
                executedPath += f"{pathSpl[i]}/"
            executedPath = executedPath[:-1]
        else:
            executedPath += f"/{guildToDo}"
    return executedPath


async def handleAllActions(bot: commands.Bot, actionData: dict, interaction: discord.Interaction | None = None,
                           ctx: discord.ext.commands.context.Context | None = None,
                           placeholders: dict = dict()):
    for action in actionData.keys():
        for doing in actionData.get(action).keys():
            executionPath = action + "/" + doing
            if doing == "messages":
                await handleActionMessages(bot, list(actionData.get(action, {}).get(doing, [])).copy(),
                                           action, executionPath, placeholders, interaction=interaction, ctx=ctx)

            elif doing == "commands":
                await handleActionCommands(bot, list(actionData.get(action, {}).get(doing, [])).copy(),
                                           executionPath, placeholders, action, interaction=interaction, ctx=ctx)

            elif doing == "user":
                await handleUser(dict(actionData.get(action, {}).get(doing, {})).copy(), bot, action,
                                 executionPath, placeholders, interaction=interaction, ctx=ctx)

            elif doing == "guild":
                await handleGuild(dict(actionData.get(action, {}).get(doing, {})).copy(), bot, action,
                                  executionPath, placeholders, interaction=interaction, ctx=ctx)


async def handleErrorActions(bot: commands.Bot, errorPath: str, interaction: discord.Interaction | None = None,
                             ctx: discord.ext.commands.context.Context | None = None,
                             placeholders: dict = dict()):
    # 'idk' -> {'messages' : [....]}
    actionData: dict = dict()
    for action in utils.configManager.getErrorActions(errorPath):
        actionData[action] = utils.configManager.getActionData(action).copy()
    await handleAllActions(bot, actionData, interaction=interaction, ctx=ctx, placeholders=placeholders)



