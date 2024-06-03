from __future__ import annotations

import asyncio
import threading
from datetime import datetime
from typing import List, Dict, Any

import discord
from discord.ext import commands
import cogs.ext.utils.utils as utils
import cogs.ext.utils.messages as messages


async def handleActionMessages(interaction: discord.Interaction, messages_names: list, commandName: str,
                               executionPath: str) -> dict:
    # action = name of the action
    # doing = messages
    statusData: dict = {}
    for msg in messages_names:
        messageData: dict = await messages.handleMessage(interaction.client, commandName, executionPath,
                                                         singleMessage=msg,
                                                         placeholders={
                                                             utils.configManager.getActionPathPlaceholder(): executionPath},
                                                         interaction=interaction)
        statusData.update(messageData)
        if not messageData["message"]:
            return statusData
    return statusData


async def handleCogCommandExecution(cog: commands.Cog, interaction: discord.Interaction,
                                    commandName: str,
                                    command: discord.app_commands.commands.ContextMenu, finalArgs: list,
                                    executionPath: str) -> dict:
    commandData: dict = {"executed": False, "execution_error": {}}
    for co in cog.get_app_commands():
        if co.name == commandName:
            try:
                await command.callback(cog, interaction, *finalArgs)
            except Exception as e:
                commandData["executed"] = False
                commandData["execution_error"] = await messages.handleError(interaction.client, commandName,
                                                                            executionPath, e,
                                                                            placeholders={}, interaction=interaction)
            else:
                commandData["executed"] = True
            return commandData
    return commandData


async def handleActionCommands(interaction: discord.Interaction, commandsData: dict, executedPath: str) -> dict:
    # command: {command status}
    commandsExecutionData: dict = dict()
    for command in commandsData.keys():
        comm: discord.app_commands.commands.ContextMenu | None = interaction.client.tree.get_command(command)
        if comm is not None:
            args = commandsData.get(command, [])
            if not isinstance(args, list):
                args = []

            executed = False
            for name, file_name in utils.configManager.getCogData().items():
                cog: commands.Cog = interaction.client.get_cog(name)
                for cogCommand in cog.get_app_commands():
                    if cogCommand.name == comm.name:
                        try:
                            await interaction.client.load_extension(f"cogs.{file_name}")
                        except commands.ExtensionAlreadyLoaded:
                            commandsExecutionData[comm] = await handleCogCommandExecution(cog, interaction, comm.name,
                                                                                          comm, args, executedPath)
                        else:
                            executed = True
                            commandsExecutionData["success"] = "Command has been executed"
                        break
                if executed:
                    break
        else:
            commandsExecutionData["error"] = "No such app command"
    return commandsExecutionData


def startBackgroundTask(**taskArgs):
    async def wait(tasks: dict):
        try:
            await asyncio.sleep(tasks["duration"])
            await tasks["function"](*tasks["functionArgs"])
        except Exception as e:
            interaction = tasks["interaction"]
            if not interaction.is_expired():
                await messages.handleError(tasks["bot"], tasks["commandName"], tasks["executedPath"], e,
                                           placeholders={}, interaction=interaction)

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


async def handleUser(interaction: discord.Interaction, userData: dict, bot: commands.Bot, commandName: str,
                     executedPath: str):
    for userDo in userData.keys():
        userDoDataList: list = userData.get(userDo, [])
        if not isinstance(userDoDataList, list):
            userDoDataList = [userDoDataList] if isinstance(userDoDataList, dict) else []
        elif len(userDoDataList) == 0:
            await messages.handleError(bot, commandName, executedPath,
                                       "Expected a map! Example: {'interact_both': False, 'user_id': ...}",
                                       placeholders={}, interaction=interaction)
            break

        checkReason = checkIFAnyValuableData(userDoDataList)
        if len(checkReason) > 0:
            await messages.handleError(bot, commandName, executedPath, checkReason,
                                       placeholders={}, interaction=interaction)
            break
        user = interaction.user
        defaultArguments = {"bot": bot, "interaction": interaction, "duration": -1, "commandName": commandName,
                            "executedPath": executedPath}
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
                                                   placeholders={}, interaction=interaction)
                    else:
                        usersBanned.append(user)

                for userToBan in utils.getUsers(userDoData, interaction.guild):
                    try:
                        await utils.banUser(userToBan, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath, {"error": e,
                                 "message": f"Couldn't ban user {userToBan.name} : {userToBan.id} for reason {reason}"},
                                                  placeholders={}, interaction=interaction)
                    else:
                        usersBanned.append(userToBan)

                duration: int = int(userDoData.get("duration", -1))
                if duration > 0 and len(usersBanned) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=actionUnbanUsers,
                                        functionArgs=[usersBanned, str(userDoData.get("unban_reason", ""))],
                                        **defaultArguments)
        elif userDo == "unban":
            for i in range(len(userDoDataList)):
                userDoData = userDoDataList[i]
                duration: int = int(userDoData.get("duration", -1))
                reason = str(userDoData.get("reason", ""))

                usersUnbanned: list = []
                if bool(userDoData.get("interact_both", True)):
                    try:
                        await utils.unbanUser(user, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"error": e, "message":
                                             f"Couldn't unban user {user.name} : {user.id} for reason {reason}"},
                                                   placeholders={}, interaction=interaction)
                    else:
                        usersUnbanned.append(user)

                for resUser in utils.getUsers(userDoData, interaction.guild):
                    try:
                        await utils.unbanUser(resUser, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"error": e,
                                                    "message":
                                    f"Couldn't unban user {resUser.name} : {resUser.id} for reason {reason}"},
                                                   placeholders={}, interaction=interaction)
                    else:
                        usersUnbanned.append(user)

                if duration > 0 and len(usersUnbanned) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=actionBanUsers,
                                        functionArgs=[usersUnbanned, str(userDoData.get("unban_reason", ""))],
                                        **defaultArguments)
        elif userDo == "kick":
            for i in range(len(userDoDataList)):
                userDoData = userDoDataList[i]
                users: list = utils.getUsers(userDoData, interaction.guild)
                reason = str(userDoData.get("reason", ""))
                if bool(userDoData.get("interact_both", True)):
                    try:
                        await utils.kickUser(user, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"error": e,
                                                    "message":
                                          f"Couldn't kick user {user.name} : {user.id} for reason {reason}"},
                                                   placeholders={}, interaction=interaction)

                for resUser in users:
                    try:
                        await utils.kickUser(resUser, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"error": e,
                                                    "message":
                                     f"Couldn't kick user {resUser.name} : {resUser.id} for reason {reason}"},
                                                   placeholders={}, interaction=interaction)
        elif userDo == "role_add":
            for i in range(len(userDoDataList)):
                userDoData = userDoDataList[i]
                duration: int = int(userDoData.get("duration", -1))
                users: list = utils.getUsers(userDoData, interaction.guild)
                reason = str(userDoData.get("reason", ""))

                roleAdded: dict = dict()
                for role in utils.getRoles(userDoData, interaction.guild):
                    roleAdded[role] = []
                    if bool(userDoData.get("interact_both", True)):
                        try:
                            await utils.addRole(user, role, reason=reason)
                        except Exception as e:
                            await messages.handleError(bot, commandName, executedPath,
                                                       {"error": e,  "message":
                  f"Couldn't add role {role.name} : {role.id} to user {user.name} : {user.id} for reason {reason}"},
                                                       placeholders={}, interaction=interaction)
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
                                                       placeholders={}, interaction=interaction)

                        else:
                            roleAdded[role].append(resUser)
                hasData = False
                for itemK, itemV in roleAdded.items():
                    if len(itemV) > 0:
                        hasData = True
                        break
                if duration > 0 and hasData:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=actionRemoveUserRoles,
                                        functionArgs=[roleAdded, str(userDoData.get("role_remove_reason", ""))],
                                        **defaultArguments)
        elif userDo == "role_remove":
            for i in range(len(userDoDataList)):
                userDoData = userDoDataList[i]
                duration: int = int(userDoData.get("duration", -1))
                users: list = utils.getUsers(userDoData, interaction.guild)
                reason = str(userDoData.get("reason", ""))

                roleRemoved: dict = dict()
                for role in utils.getRoles(userDoData, interaction.guild):
                    roleRemoved[role] = []
                    if bool(userDoData.get("interact_both", True)):
                        try:
                            await utils.removeRole(user, role, reason=reason)
                        except Exception as e:
                            await messages.handleError(bot, commandName, executedPath,
                                                       {"error": e,"message":
           f"Couldn't remove role {role.name} : {role.id} to user {user.name} : {user.id} for reason {reason}"},
                                                       placeholders={}, interaction=interaction)
                        else:
                            roleRemoved[role].append(user)
                    for resUser in users:
                        try:
                            await utils.removeRole(resUser, role, reason=reason)
                        except Exception as e:
                            await messages.handleError(bot, commandName, executedPath,
                                                       {"error": e, "message":
            f"Couldn't remove role {role.name} : {role.id} to user {resUser.name} : {resUser.id} for reason {reason}"},
                                                       placeholders={}, interaction=interaction)
                        else:
                            roleRemoved[role].append(resUser)
                hasData = False
                for itemK, itemV in roleRemoved.items():
                    if len(itemV) > 0:
                        hasData = True
                        break
                if duration > 0 and hasData:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=actionAddUserRoles,
                                        functionArgs=[roleRemoved, str(userDoData.get("role_add_reason", ""))],
                                        **defaultArguments)
        elif userDo == "timeout":
            for i in range(len(userDoDataList)):
                userDoData = userDoDataList[i]
                duration: int = int(userDoData.get("duration", -1))
                reason = str(userDoData.get("reason", ""))
                if "until" not in userDoData.keys():
                    await messages.handleError(bot, commandName, executedPath,
                                               "Until data is invalid! Format expected: YYYY-MM-DDTHH:MM:SS",
                                               placeholders={}, interaction=interaction)
                    break
                else:
                    try:
                        strptime = datetime.strptime(str(userDoData.get("until")), "YYYY-MM-DDTHH:MM:SS")
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"error": e, "message":
                            "Until data is invalid! Format expected: YYYY-MM-DDTHH:MM:SS"},
                                                   placeholders={}, interaction=interaction)
                        break
                timeoutedMembers: list = []
                if bool(userDoData.get("interact_both", True)):
                    try:
                        await utils.timeoutUser(user, strptime, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"error": e, "message":
                         f"Couldn't timeout user {user.name} : {user.id} to date {strptime}"},
                                                   placeholders={}, interaction=interaction)

                    else:
                        timeoutedMembers.append(user)
                for resUser in utils.getUsers(userDoData, interaction.guild):
                    try:
                        await utils.timeoutUser(resUser, strptime, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"error": e, "message":
                                  f"Couldn't timeout user {resUser.name} : {resUser.id} to date {strptime}"},
                                                   placeholders={}, interaction=interaction)
                    else:
                        timeoutedMembers.append(resUser)
                if duration > 0 and len(timeoutedMembers) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=actionRemoveUserTimeout,
                                        functionArgs=[timeoutedMembers,
                                                      str(userDoData.get("timeout_remove_reason", ""))],
                                        **defaultArguments)
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
                                 f"Couldn't deafen user {user.name} : {user.id} for reason {reason}", "error": e},
                                                   placeholders={}, interaction=interaction)
                    else:
                        deafenMembers.append(user)
                for resUser in utils.getUsers(userDoData, interaction.guild):
                    try:
                        await utils.userDeafen(resUser, True, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"message":
                                f"Couldn't deafen user {resUser.name} : {resUser.id} for reason {reason}", "error": e},
                                                   placeholders={}, interaction=interaction)
                    else:
                        deafenMembers.append(resUser)

                if duration > 0 and len(deafenMembers) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=actionRemoveUserDeafen,
                                        functionArgs=[deafenMembers, str(userDoData.get("deafen_remove_reason", ""))],
                                        **defaultArguments)
        elif userDo == "deafen_remove":
            for i in range(len(userDoDataList)):
                userDoData = userDoDataList[i]
                duration: int = int(userDoData.get("duration", -1))
                users: list = utils.getUsers(userDoData, interaction.guild)
                reason = str(userDoData.get("reason", ""))

                removeDeafenMembers: list = []
                if bool(userDoData.get("interact_both", True)):
                    try:
                        await utils.userDeafen(user, False, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"message":
                                 f"Couldn't undeafen user {user.name} : {user.id} for reason {reason}", "error": e},
                                                   placeholders={}, interaction=interaction)
                    else:
                        removeDeafenMembers.append(user)
                for resUser in users:
                    try:
                        await utils.userDeafen(resUser, False, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"error": e,"message":
                                         f"Couldn't undeafen user {resUser.name} : {resUser.id} for reason {reason}"},
                                                   placeholders={}, interaction=interaction)
                    else:
                        removeDeafenMembers.append(resUser)

                if duration > 0 and len(removeDeafenMembers) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=actionUserDeafen,
                                        functionArgs=[removeDeafenMembers, str(userDoData.get("deafen_reason", ""))],
                                        **defaultArguments)
        elif userDo == "mute":
            for i in range(len(userDoDataList)):
                userDoData = userDoDataList[i]
                duration: int = int(userDoData.get("duration", -1))
                users: list = utils.getUsers(userDoData, interaction.guild)
                reason = str(userDoData.get("reason", ""))
                removeMutedMembers: list = []

                if bool(userDoData.get("interact_both", True)):
                    try:
                        await utils.userMute(user, True, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"message":
                        f"Couldn't muted user {user.name} : {user.id} for reason {reason}", "error": e},
                                                   placeholders={}, interaction=interaction)
                    else:
                        removeMutedMembers.append(user)
                for resUser in users:
                    try:
                        await utils.userMute(resUser, True, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"message":
                                 f"Couldn't muted user {resUser.name} | {resUser.id} for reason {reason}", "error": e},
                                                   placeholders={}, interaction=interaction)
                    else:
                        removeMutedMembers.append(resUser)

                if duration > 0 and len(removeMutedMembers) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=actionRemoveUserMute,
                                        functionArgs=[removeMutedMembers,
                                                      str(userDoData.get("mute_remove_reason", ""))],
                                        **defaultArguments)
        elif userDo == "mute_remove":
            for i in range(len(userDoDataList)):
                userDoData = userDoDataList[i]
                duration: int = int(userDoData.get("duration", -1))
                users: list = utils.getUsers(userDoData, interaction.guild)
                reason = str(userDoData.get("reason", ""))
                removeMutedMembers: list = []
                if bool(userDoData.get("interact_both", True)):
                    try:
                        await utils.userMute(user, False, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"error": e,
                                    "message": f"Couldn't unmute user {user.name} | {user.id} for reason {reason}"},
                                                   placeholders={}, interaction=interaction)
                    else:
                        removeMutedMembers.append(user)

                for resUser in users:
                    try:
                        await utils.userMute(resUser, False, reason=reason)
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"error": e,
                               "message": f"Couldn't unmute user {resUser.name} | {resUser.id} for reason {reason}"},
                                                   placeholders={}, interaction=interaction)
                    else:
                        removeMutedMembers.append(resUser)

                if duration > 0 and len(removeMutedMembers) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=actionUserMute,
                                        functionArgs=[removeMutedMembers, str(userDoData.get("mute_reason", ""))],
                                        **defaultArguments)


async def handleGuild(interaction: discord.Interaction, guildData: dict, bot: commands.Bot, commandName: str,
                      executedPath: str):
    guild = interaction.guild
    defaultArguments = {"bot": bot, "interaction": interaction, "duration": -1, "commandName": commandName,
                        "executedPath": executedPath}
    for guildToDo in guildData.keys():
        listData = guildData.get(guildToDo, [])
        if not isinstance(listData, list):
            listData = [listData] if isinstance(listData, dict) else []
        elif len(listData) == 0:
            await messages.handleError(bot, commandName, executedPath,
                        "No data has been provided. Expected map! Example: {'role_id': ..., 'role_name':...}",
                                       placeholders={}, interaction=interaction)
            break

        checkReason = checkIFAnyValuableData(listData)
        if len(checkReason) > 0:
            await messages.handleError(bot, commandName, executedPath, checkReason, placeholders={},
                                       interaction=interaction)
            break

        guild_id = guild.id
        guild_name = guild.name
        if guildToDo == "role_create":
            for i in range(len(listData)):
                rolesData: dict = listData[i]
                try:
                    role = await utils.createRole(rolesData, guild)
                except Exception as e:
                    await messages.handleError(bot, commandName, executedPath,
                                               {"error": e,"message":
                                 f"Couldn't create role {rolesData.get('name')} for reason {rolesData.get('reason')} "
                                                    f"in guild {guild_name} : {guild_id}"},
                                               placeholders={}, interaction=interaction)
                    continue
                duration: int = int(rolesData.get("duration", -1))
                if duration > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=utils.deleteRole,
                                        functionArgs=[role, str(rolesData.get("role_delete_reason", ""))],
                                        **defaultArguments)
        elif guildToDo == "role_delete":
            for i in range(len(listData)):
                rolesData = listData[i]
                roles: list = []
                for selectedRole in utils.getRoles(rolesData, interaction.guild):
                    try:
                        await utils.deleteRole(selectedRole, reason=rolesData.get("reason", ""))
                    except Exception as e:
                        await messages.handleError(bot, commandName, executedPath,
                                                   {"error": e, "message":
                                     f"Couldn't delete role {selectedRole.name} : {selectedRole.id} " +
                                       f"for reason {rolesData.get('reason')} in guild {guild_name} : {guild_id}"},
                                                   placeholders={}, interaction=interaction)
                    else:
                        roles.append(selectedRole)
                duration: int = int(rolesData.get("duration", -1))
                if duration > 0 and len(roles) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=actionCreateRole,
                                        functionArgs=[roles, str(rolesData.get("role_create_reason", "")),
                                                      bool(rolesData.get("give_back_roles_to_users", False)),
                                                      str(rolesData.get("give_back_reason", "")), guild],
                                        **defaultArguments)
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
                            f"Couldn't edit role {role.name} : {role.id} for reason {rolesData.get('reason')} " +
                                                        f"in guild {guild_name} : {guild_id}"},
                                                   placeholders={}, interaction=interaction)
                    else:
                        edited[role] = prevStatus
                duration: int = int(rolesData.get("duration", -1))
                if duration > 0 and len(edited) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=actionRoleEdit,
                                        functionArgs=[edited, str(rolesData.get("role_edit_reason", ""))],
                                        **defaultArguments)
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
                                                f"Couldn't edit guild {guild_name} : {guild_id} for reason {reason}"},
                                               placeholders={}, interaction=interaction)
                    continue

                prevData: dict = dict()
                for key in overviewData.keys():
                    if key not in fullPrevData.keys():
                        continue
                    prevData[key] = fullPrevData.get(key)
                duration: int = int(overviewData.get("duration", -1))
                if duration > 0 and len(prevData) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=utils.editGuild,
                                        functionArgs=[prevData, guild, str(overviewData.get("guild_edit_reason", ""))],
                                        **defaultArguments)
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
                                               placeholders={}, interaction=interaction)

                    continue
                duration: int = int(categoryData.get("duration", -1))
                if duration > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=utils.deleteCategory,
                                        functionArgs=[category, str(categoryData.get("category_delete_reason", ""))],
                                        **defaultArguments)
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
                                                   placeholders={}, interaction=interaction)
                    else:
                        deletedCategories.append(category)

                duration: int = int(categoryData.get("duration", -1))
                if duration > 0 and len(deletedCategories) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=actionCategoryCreate,
                                        functionArgs=[deletedCategories,
                                                      str(categoryData.get("category_delete_reason", "")), guild],
                                        **defaultArguments)
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
                                                   placeholders={}, interaction=interaction)
                    else:
                        editedCategories[category] = categoryPrevData

                duration: int = int(categoryData.get("duration", -1))
                if duration > 0 and len(editedCategories) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=actionCategoryEdit,
                                        functionArgs=[editedCategories,
                                                      str(categoryData.get("category_edit_reason", ""))],
                                        **defaultArguments)
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
                                               placeholders={}, interaction=interaction)
                    continue

                duration: int = int(channelData.get("duration", -1))
                if duration > 0 and len(channels) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=actionChannelDelete,
                                        functionArgs=[channels,
                                                      str(channelData.get("channel_delete_reason", ""))],
                                        **defaultArguments)
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
                                                   placeholders={}, interaction=interaction)
                    else:
                        deletedChannels.append(channel)
                duration: int = int(channelData.get("duration", -1))
                if duration > 0 and len(deletedChannels) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=actionChannelCreate,
                                        functionArgs=[deletedChannels,
                                                      str(channelData.get("channel_create_reason", ""))],
                                        **defaultArguments)
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
                                                   placeholders={}, interaction=interaction)
                    else:
                        editedChannels[channel] = channelPrevData

                duration: int = int(channelData.get("duration", -1))
                if duration > 0 and len(editedChannels) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=actionChannelEdit,
                                        functionArgs=[editedChannels,
                                                      str(channelData.get("channel_edit_reason", ""))],
                                        **defaultArguments)


async def handleAllActions(bot: commands.Bot, actionData: dict, interaction: discord.Interaction) -> dict:
    resultData: dict = dict()
    for action in actionData.keys():
        resultData[action] = dict()
        for doing in actionData.get(action).keys():
            resultData[action][doing] = dict()
            executionPath = action + "/" + doing
            resultData[action][doing]["execution_path"] = executionPath
            if doing == "messages":
                resultData[action][doing]["status"] = await handleActionMessages(interaction,
                                                                                 list(actionData.get(action, {})
                                                                                      .get(doing, [])).copy(),
                                                                                 action, executionPath)

            elif doing == "commands":
                resultData[action][doing]["status"] = await handleActionCommands(interaction,
                                                                                 dict(actionData.get(action, {})
                                                                                      .get(doing, {})).copy(),
                                                                                 executionPath)

            elif doing == "user":
                resultData[action][doing]["status"] = await handleUser(interaction,
                                                                       dict(actionData.get(action, {})
                                                                            .get(doing, {})).copy(),
                                                                       bot, action, executionPath)

            elif doing == "guild":
                resultData[action][doing]["status"] = await handleGuild(interaction,
                                                                        dict(actionData.get(action, {})
                                                                             .get(doing, {})).copy(),
                                                                        bot, action, executionPath)
    return resultData


async def handleErrorActions(bot: commands.Bot, errorPath: str, interaction: discord.Interaction) -> dict:
    # 'idk' -> {'messages' : [....]}
    actionData: dict = dict()
    for action in utils.configManager.getErrorActions(errorPath):
        actionData[action] = utils.configManager.getActionData(action).copy()
    return await handleAllActions(bot, actionData, interaction)









