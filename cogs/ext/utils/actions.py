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
            finally:
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

            for name, file_name in utils.configManager.getCogData().items():
                cog: commands.Cog = interaction.client.get_cog(name)
                found = False
                for cogCommand in cog.get_app_commands():
                    if cogCommand.name == comm.name:
                        try:
                            await interaction.client.load_extension(f"cogs.{file_name}")
                        except commands.ExtensionAlreadyLoaded:
                            commandsExecutionData[comm] = await handleCogCommandExecution(cog, interaction, comm.name,
                                                                                          comm, args, executedPath)
                        found = True
                        break
                if found:
                    break
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
        roleCreated = await utils.createRoleWithDisplayIcon(roleData, guild)
        if roleCreated is None:
            roleCreated = await utils.createRoleNoDisplayIcon(roleData, guild)
            if roleCreated is None:
                raise Exception(f"Couldn't create a role with this data: {roleData}")
        if "users" not in roleData.keys() or len(roleData.get("users", [])) == 0:
            continue
        for userId in roleData.get("users", []):
            member: discord.Member | None = utils.getMemberGuild(guild, userId)
            if member is None:
                raise Exception(f"Couldn't find member with ID {userId} in {guild.name} : {guild.id} guild")
            await utils.addRole(member, roleCreated, reason=give_back_reason)


async def actionRoleEdit(roles: Dict[discord.Role, Dict], reason: str):
    for editedRole, prevData in roles.items():
        prevData["reason"] = reason
        prevData["new_name"] = prevData.pop("name")
        roleStatus: dict = await utils.editRole(prevData, editedRole)


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


async def actionChannelCreate(channels: list, reason: str):
    for channelToDel in channels:
        data: dict = utils.getChannelData(channelToDel)
        data["reason"] = reason
        try:
            await utils.createChannel(data, channelToDel.guild)
        except Exception:
            continue


async def handleUser(interaction: discord.Interaction, userData: dict, bot: commands.Bot, commandName: str,
                     executedPath: str) -> dict:
    userStatus: dict = dict()
    for userDo in userData.keys():
        userStatus[userDo] = dict()
        userStatus[userDo]["action_user_data"] = dict()
        userDoDataList: list = userData.get(userDo, [])
        if not isinstance(userDoDataList, list):
            userDoDataList = [userDoDataList] if isinstance(userDoDataList, dict) else []
        elif len(userDoDataList) == 0:
            userStatus[userDo]["error"] = "Expected a map! Example: {'interact_both': False, 'user_id': ...}"
            break

        checkReason = checkIFAnyValuableData(userDoDataList)
        if len(checkReason) > 0:
            userStatus[userDo]["error"] = checkReason
            break

        userStatus[userDo]["action_user_data"] = userDoDataList
        user = interaction.user
        userStatus[userDo]["involved_user_name"] = user.name
        userStatus[userDo]["involved_user_id"] = user.id
        defaultArguments = {"bot": bot, "interaction": interaction, "duration": -1, "commandName": commandName,
                            "executedPath": executedPath}
        if userDo == "ban":
            for i in range(len(userDoDataList)):
                userDoData = userDoDataList[i]
                userStatus[userDo][i] = dict()
                reason = str(userDoData.get("reason", ""))

                usersBanned: list = []
                if bool(userDoData.get("interact_both", True)):
                    try:
                        await utils.banUser(user, reason=reason)
                    except Exception as e:
                        userStatus[userDo][i]["user_ban_error"] = {"error": e,
                                 "message": f"Couldn't ban user {user.name} : {user.id} for reason {reason}"}
                    finally:
                        userStatus[userDo][i]["user_ban_success"] = \
                            {"message": f"Banned {user.name} : {user.id} for reason {reason}"}
                        usersBanned.append(user)

                userStatus[userDo][i]["ban_success"] = []
                userStatus[userDo][i]["ban_error"] = []
                for userToBan in utils.getUsers(userDoData, interaction.guild):
                    try:
                        await utils.banUser(userToBan, reason=reason)
                    except Exception as e:
                        userStatus[userDo][i]["ban_error"].append({"error": e,
                                 "message": f"Couldn't ban user {user.name} : {user.id} for reason {reason}"})
                    finally:
                        userStatus[userDo][i]["ban_success"].append(
                            {"message": f"Banned {user.name} : {user.id} for reason {reason}"})
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
                userStatus[userDo][i] = dict()
                duration: int = int(userDoData.get("duration", -1))
                reason = str(userDoData.get("reason", ""))

                usersUnbanned: list = []
                if bool(userDoData.get("interact_both", True)):
                    try:
                        await utils.unbanUser(user, reason=reason)
                    except Exception as e:
                        userStatus[userDo]["user_unban_error"] = {"error": e,
                                                                "message":
                                             f"Couldn't unban user {user.name} : {user.id} for reason {reason}"}
                    finally:
                        userStatus[userDo]["user_unban_success"] = \
                            {"message": f"Unbanned {user.name} : {user.id} for reason {reason}"}
                        usersUnbanned.append(user)

                userStatus[userDo]["unban_error"] = []
                userStatus[userDo]["unban_success"] = []
                for resUser in utils.getUsers(userDoData, interaction.guild):
                    try:
                        await utils.unbanUser(resUser, reason=reason)
                    except Exception as e:
                        userStatus[userDo]["unban_error"].append({"error": e,
                                                                "message":
                                       f"Couldn't unban user {resUser.name} : {resUser.id} for reason {reason}"})
                    finally:
                        userStatus[userDo]["unban_success"].append({"message":
                                                    f"Unbanned {resUser.name} : {resUser.id} for reason {reason}"})
                        usersUnbanned.append(user)

                if duration > 0 and len(usersUnbanned) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=actionBanUsers,
                                        functionArgs=[usersUnbanned, str(userDoData.get("unban_reason", ""))],
                                        **defaultArguments)
        elif userDo == "kick":
            for i in range(len(userDoDataList)):
                userDoData = userDoDataList[i]
                userStatus[userDo][i] = dict()
                users: list = utils.getUsers(userDoData, interaction.guild)
                reason = str(userDoData.get("reason", ""))
                if bool(userDoData.get("interact_both", True)):
                    try:
                        await utils.kickUser(user, reason=reason)
                    except Exception as e:
                        userStatus[userDo][i]["user_kick_error"] = {"error": e,
                                                                "message":
                                    f"Couldn't kick user {user.name} : {user.id} for reason {reason}"}
                    finally:
                        userStatus[userDo][i]["user_kick_success"] = \
                            {"message": f"Kicked {user.name} : {user.id} for reason {reason}"}

                userStatus[userDo][i]["kick_error"] = []
                userStatus[userDo][i]["kick_success"] = []
                for resUser in users:
                    try:
                        await utils.kickUser(resUser, reason=reason)
                    except Exception as e:
                        userStatus[userDo][i]["kick_error"].append({"error": e,
                                                                 "message":
                         f"Couldn't kick user {resUser.name} : {resUser.id} for reason {reason}"})
                    finally:
                        userStatus[userDo][i]["kick_success"].append({"message":
                                          f"Kicked {resUser.name} : {resUser.id} for reason {reason}"})
        elif userDo == "role_add":
            for i in range(len(userDoDataList)):
                userDoData = userDoDataList[i]
                userStatus[userDo][i] = dict()
                duration: int = int(userDoData.get("duration", -1))
                users: list = utils.getUsers(userDoData, interaction.guild)
                reason = str(userDoData.get("reason", ""))

                roleAdded: dict = dict()
                userStatus[userDo][i]["user_role_add_error"] = []
                userStatus[userDo][i]["user_role_add_success"] = []

                userStatus[userDo][i]["role_add_success"] = []
                userStatus[userDo][i]["role_add_error"] = []
                for role in utils.getRoles(userDoData, interaction.guild):
                    roleAdded[role] = []
                    if bool(userDoData.get("interact_both", True)):
                        try:
                            await utils.addRole(user, role, reason=reason)
                        except Exception as e:
                            userStatus[userDo][i]["user_role_add_error"].append(
                                {"error": e,
                                 "message":
              f"Couldn't add role {role.name} : {role.id} to user {user.name} : {user.id} for reason {reason}"})
                        finally:
                            userStatus[userDo][i]["user_role_add_success"].append(
                                {"message":
                          f"Added role {role.name} : {role.id} to user {user.name} : {user.id} for reason {reason}"})
                            roleAdded[role].append(user)

                    for resUser in users:
                        try:
                            await utils.addRole(resUser, role, reason=reason)
                        except Exception as e:
                            userStatus[userDo][i]["role_add_error"].append({"error": e,
                                 "message":
                f"Couldn't add role {role.name} : {role.id} to user {resUser.name} : {resUser.id} for reason {reason}"})
                        finally:
                            userStatus[userDo][i]["role_add_success"].append(
                                {"message":
                  f"Added role {role.name} : {role.id} to user {resUser.name} : {resUser.id} for reason {reason}"})
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
                userStatus[userDo][i] = dict()
                duration: int = int(userDoData.get("duration", -1))
                users: list = utils.getUsers(userDoData, interaction.guild)
                reason = str(userDoData.get("reason", ""))

                roleRemoved: dict = dict()
                userStatus[userDo][i]["user_role_remove_error"] = []
                userStatus[userDo][i]["user_role_remove_success"] = []

                userStatus[userDo][i]["role_remove_error"] = []
                userStatus[userDo][i]["role_remove_success"] = []
                for role in utils.getRoles(userDoData, interaction.guild):
                    roleRemoved[role] = []
                    if bool(userDoData.get("interact_both", True)):
                        try:
                            await utils.removeRole(user, role, reason=reason)
                        except Exception as e:
                            userStatus[userDo][i]["user_role_remove_error"].append(
                                {"error": e,
                                 "message":
            f"Couldn't remove role {role.name} : {role.id} to user {user.name} : {user.id} for reason {reason}"})
                        finally:
                            userStatus[userDo][i]["user_role_remove_success"].append(
                                {"message":
                     f"Removed role {role.name} : {role.id} to user {user.name} : {user.id} for reason {reason}"})
                            roleRemoved[role].append(user)
                    for resUser in users:
                        try:
                            await utils.removeRole(resUser, role, reason=reason)
                        except Exception as e:
                            userStatus[userDo][i]["role_remove_error"].append(
                                {"error": e,
                                 "message":
           f"Couldn't remove role {role.name} : {role.id} to user {resUser.name} : {resUser.id} for reason {reason}"})
                        finally:
                            roleRemoved[role].append(resUser)
                            userStatus[userDo][i]["role_remove_success"].append(
                                {"message":
              f"Removed role {role.name} : {role.id} to user {resUser.name} : {resUser.id} for reason {reason}"})
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
                userStatus[userDo][i] = dict()
                duration: int = int(userDoData.get("duration", -1))
                reason = str(userDoData.get("reason", ""))
                if "until" not in userDoData.keys():
                    userStatus[userDo][i]["error"] = "Until data is invalid! Format expected: YYYY-MM-DDTHH:MM:SS"
                    break
                else:
                    try:
                        strptime = datetime.strptime(str(userDoData.get("until")), "YYYY-MM-DDTHH:MM:SS")
                    except Exception as e:
                        userStatus[userDo][i]["error"] = {"error": e, "message":
                            "Until data is invalid! Format expected: YYYY-MM-DDTHH:MM:SS"}
                        break
                timeoutedMembers: list = []
                if bool(userDoData.get("interact_both", True)):
                    try:
                        await utils.timeoutUser(user, strptime, reason=reason)
                    except Exception as e:
                        userStatus[userDo][i]["user_timeout_add_error"] = \
                            {"error": e,
                             "message":
                                 f"Couldn't timeout user {user.name} : {user.id} to date {strptime}"}
                    finally:
                        userStatus[userDo][i]["user_timeout_add_success"] = \
                            {"message":  f"Added timeout to user {user.name} : {user.id} to date {strptime}"}
                        timeoutedMembers.append(user)
                userStatus[userDo][i]["timeout_add_error"] = []
                userStatus[userDo][i]["timeout_add_success"] = []
                for resUser in utils.getUsers(userDoData, interaction.guild):
                    try:
                        await utils.timeoutUser(resUser, strptime, reason=reason)
                    except Exception as e:
                        userStatus[userDo][i]["timeout_add_error"].append(
                            {"error": e,
                             "message":
                                 f"Couldn't timeout user {resUser.name} : {resUser.id} to date {strptime}"})
                    finally:
                        userStatus[userDo][i]["timeout_add_success"].append(
                            {"message": f"Added timeout to user {resUser.name} : {resUser.id} to date {strptime}"})
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
                userStatus[userDo][i] = dict()
                duration: int = int(userDoData.get("duration", -1))
                reason = str(userDoData.get("reason", ""))

                deafenMembers: list = []
                if bool(userDoData.get("interact_both", True)):
                    try:
                        await utils.userDeafen(user, True, reason=reason)
                    except Exception as e:
                        userStatus[userDo][i]["user_deafen_add_error"] = \
                            {"message": f"Couldn't deafen user {user.name} : {user.id} for reason {reason}",
                             "error": e}
                    finally:
                        userStatus[userDo][i]["user_deafen_add_success"] = \
                            {"message": f"Made user {user.name} : {user.id} deafen for reason {reason}"}
                        deafenMembers.append(user)
                userStatus[userDo][i]["deafen_add_error"] = []
                userStatus[userDo][i]["deafen_add_success"] = []
                for resUser in utils.getUsers(userDoData, interaction.guild):
                    userStatus[userDo][i]["deafen_add_success"] = []
                    try:
                        await utils.userDeafen(user, True, reason=reason)
                    except Exception as e:
                        userStatus[userDo][i]["deafen_add_error"].append(
                            {"message": f"Couldn't deafen user {user.name} : {user.id} for reason {reason}",
                             "error": e})
                    finally:
                        userStatus[userDo][i]["deafen_add_success"].append(
                            {"message": f"Made user {user.name} : {user.id} deafen for reason {reason}"})
                        deafenMembers.append(resUser)

                if duration > 0 and len(deafenMembers) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=actionRemoveUserDeafen,
                                        functionArgs=[deafenMembers, str(userDoData.get("deafen_remove_reason", ""))],
                                        **defaultArguments)
        elif userDo == "deafen_remove":
            for i in range(len(userDoDataList)):
                userDoData = userDoDataList[i]
                userStatus[userDo][i] = dict()
                duration: int = int(userDoData.get("duration", -1))
                users: list = utils.getUsers(userDoData, interaction.guild)
                reason = str(userDoData.get("reason", ""))

                removeDeafenMembers: list = []
                if bool(userDoData.get("interact_both", True)):
                    try:
                        await utils.userDeafen(user, False, reason=reason)
                    except Exception as e:
                        userStatus[userDo][i]["user_deafen_remove_error"] = \
                            {"message": f"Couldn't undeafen user {user.name} : {user.id} for reason {reason}",
                             "error": e}
                    finally:
                        userStatus[userDo][i]["user_deafen_remove_success"] = \
                            {"message": f"Undeafen user {user.name} : {user.id} for reason {reason}"}
                        removeDeafenMembers.append(user)
                userStatus[userDo][i]["deafen_remove_success"] = []
                userStatus[userDo][i]["deafen_remove_error"] = []
                for resUser in users:
                    try:
                        await utils.userDeafen(resUser, False, reason=reason)
                    except Exception as e:
                        userStatus[userDo][i]["deafen_remove_error"].append({"error": e,
                                 "message":
                                     f"Couldn't undeafen user {resUser.name} : {resUser.id} for reason {reason}"})
                    finally:
                        userStatus[userDo][i]["deafen_remove_success"].append({"error": e,
                                  "message":
                                      f"Uundeafened user {resUser.name} : {resUser.id} for reason {reason}"})
                        removeDeafenMembers.append(resUser)

                if duration > 0 and len(removeDeafenMembers) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=actionUserDeafen,
                                        functionArgs=[removeDeafenMembers, str(userDoData.get("deafen_reason", ""))],
                                        **defaultArguments)
        elif userDo == "mute":
            for i in range(len(userDoDataList)):
                userDoData = userDoDataList[i]
                userStatus[userDo][i] = dict()
                duration: int = int(userDoData.get("duration", -1))
                users: list = utils.getUsers(userDoData, interaction.guild)
                reason = str(userDoData.get("reason", ""))
                removeMutedMembers: list = []

                if bool(userDoData.get("interact_both", True)):
                    try:
                        await utils.userMute(user, True, reason=reason)
                    except Exception as e:
                        userStatus[userDo][i]["user_mute_add_error"] = {"message":
                                   f"Couldn't muted user {user.name} | {user.id} for reason {reason}", "error": e}
                    finally:
                        userStatus[userDo][i]["user_mute_add_success"] = {"message":
                                              f"Muted user {user.name} | {user.id} for reason {reason}"}
                        removeMutedMembers.append(user)
                userStatus[userDo][i]["mute_add_error"] = []
                userStatus[userDo][i]["mute_add_success"] = []
                for resUser in users:
                    try:
                        await utils.userMute(resUser, True, reason=reason)
                    except Exception as e:
                        userStatus[userDo][i]["mute_add_error"].append({"message":
                                   f"Couldn't muted user {user.name} | {user.id} for reason {reason}", "error": e})
                    finally:
                        userStatus[userDo][i]["mute_add_success"].append({"message":
                                             f"Muted user {resUser.name} | {resUser.id} for reason {reason}"})
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
                userStatus[userDo][i] = dict()
                duration: int = int(userDoData.get("duration", -1))
                users: list = utils.getUsers(userDoData, interaction.guild)
                reason = str(userDoData.get("reason", ""))

                removeMutedMembers: list = []
                if bool(userDoData.get("interact_both", True)):
                    try:
                        await utils.userMute(user, False, reason=reason)
                    except Exception as e:
                        userStatus[userDo][i]["user_mute_remove_error"] = {"error": e,
                                  "message": f"Couldn't unmute user {user.name} | {user.id} for reason {reason}"}
                    finally:
                        userStatus[userDo][i]["user_mute_remove_success"] = {
                                  "message": f"Unmuted user {user.name} | {user.id} for reason {reason}"}
                        removeMutedMembers.append(user)

                userStatus[userDo][i]["mute_remove_success"] = []
                userStatus[userDo][i]["mute_remove_error"] = []
                for resUser in users:
                    try:
                        await utils.userMute(resUser, False, reason=reason)
                    except Exception as e:
                        userStatus[userDo][i]["mute_remove_error"].append({"error": e,
                        "message": f"Couldn't unmute user {resUser.name} | {resUser.id} for reason {reason}"})
                    finally:
                        userStatus[userDo][i]["mute_remove_success"] = {
                            "message": f"Unmuted user {resUser.name} | {resUser.id} for reason {reason}"}
                        removeMutedMembers.append(resUser)

                if duration > 0 and len(removeMutedMembers) > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=actionUserMute,
                                        functionArgs=[removeMutedMembers, str(userDoData.get("mute_reason", ""))],
                                        **defaultArguments)
    return userStatus


async def handleGuild(interaction: discord.Interaction, guildData: dict, bot: commands.Bot, commandName: str,
                      executedPath: str):
    guildStatus: dict = dict()
    guild = interaction.guild
    guildId = guild.id

    guildStatus[guildId] = dict()
    guildStatus[guildId]["status_guild_name"] = interaction.guild.name
    defaultArguments = {"bot": bot, "interaction": interaction, "duration": -1, "commandName": commandName,
                        "executedPath": executedPath}
    for guildToDo in guildData.keys():
        # TODO finish this
        listData = guildData.get(guildToDo, [])
        if not isinstance(listData, list):
            listData = [listData] if isinstance(listData, dict) else []
        elif len(listData) == 0:
            guildStatus[guildId]["error"] = \
                "No data has been provided. Expected map! Example: {'role_id': ..., 'role_name':...}"
            break

        checkReason = checkIFAnyValuableData(listData)
        if len(checkReason) > 0:
            guildStatus[guildId]["error"] = checkReason
            break

        if guildToDo == "role_create":
            for rolesToCreate in listData:
                role = await utils.createRoleWithDisplayIcon(rolesToCreate, guild)
                if role is None:
                    role = await utils.createRoleNoDisplayIcon(rolesToCreate, guild)
                    if role is None:
                        continue
                duration: int = int(rolesToCreate.get("duration", -1))
                if duration > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=utils.deleteRole,
                                        functionArgs=[role, str(rolesToCreate.get("role_delete_reason", ""))],
                                        **defaultArguments)
        elif guildToDo == "role_delete":
            for rolesToDelete in listData:
                duration: int = int(rolesToDelete.get("duration", -1))
                roles: list = []
                for selectedRole in utils.getRoles(rolesToDelete, interaction.guild):
                    res: bool = await utils.deleteRoleFromData(selectedRole, guild)
                    if res:
                        roles.append(selectedRole)
                if duration > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=actionCreateRole,
                                        functionArgs=[roles, str(rolesToDelete.get("role_create_reason", "")),
                                                      bool(rolesToDelete.get("give_back_roles_to_users", False)),
                                                      str(rolesToDelete.get("give_back_reason", ""))],
                                        **defaultArguments)
        elif guildToDo == "role_edit":
            for rolesToEdit in listData:
                roles: List[discord.Role] = utils.getRoles(rolesToEdit, guild)
                edited: dict[discord.Role, dict] = dict()
                for role in roles:
                    prevStatus: dict = utils.getRoleData(role)
                    roleEditData: dict = await utils.editRole(rolesToEdit, role)
                    if roleEditData["role_edit"]:
                        edited[role] = prevStatus
                duration: int = int(rolesToEdit.get("duration", -1))
                if duration > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=actionRoleEdit,
                                        functionArgs=[edited, str(rolesToEdit.get("role_edit_reason", ""))],
                                        **defaultArguments)
        elif guildToDo == "overview":
            for overviewData in listData:
                fullPrevData: dict = utils.getGuildData(guild)
                res: bool = await utils.editGuild(overviewData, guild, str(overviewData.get("reason", "")))
                prevData: dict = dict()
                if not res:
                    continue
                for key in overviewData.keys():
                    if key not in fullPrevData.keys():
                        continue
                    prevData[key] = fullPrevData.get(key)
                duration: int = int(overviewData.get("duration", -1))
                if duration > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=utils.editGuild,
                                        functionArgs=[guild, prevData, str(overviewData.get("edit_reason", ""))],
                                        **defaultArguments)
        elif guildToDo == "category_create":
            for categoryData in listData:
                category: discord.CategoryChannel | None = await utils.createCategory(categoryData, guild)
                if category is None:
                    continue
                duration: int = int(categoryData.get("duration", -1))
                if duration > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=utils.deleteCategory,
                                        functionArgs=[category, str(categoryData.get("category_delete_reason", ""))],
                                        **defaultArguments)
        elif guildToDo == "category_delete":
            for categoryData in listData:
                deletedCategories: List[discord.CategoryChannel] = []
                for category in utils.getCategories(categoryData, guild):
                    if category is None:
                        continue
                    res: bool = await utils.deleteCategory(category, reason=str(categoryData.get("reason", "")))
                    if res:
                        deletedCategories.append(category)

                duration: int = int(categoryData.get("duration", -1))
                if duration > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=actionCategoryCreate,
                                        functionArgs=[deletedCategories,
                                                      str(categoryData.get("category_delete_reason", "")), guild],
                                        **defaultArguments)
        elif guildToDo == "category_edit":
            for categoryData in listData:
                editedCategories: Dict[discord.CategoryChannel, dict] = dict()
                for category in utils.getCategories(categoryData, guild):
                    if category is None:
                        continue
                    categoryPrevData: dict = utils.getCategoryData(category)
                    res: bool = await utils.editCategory(category, categoryData)
                    if res:
                        editedCategories[category] = categoryPrevData

                duration: int = int(categoryData.get("duration", -1))
                if duration > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=actionCategoryEdit,
                                        functionArgs=[editedCategories,
                                                      str(categoryData.get("category_edit_reason", ""))],
                                        **defaultArguments)
        elif guildToDo == "channel_create":
            for channelData in listData:
                channels: list = await utils.createChannel(channelData, guild)
                if len(channels) == 0:
                    continue
                duration: int = int(channelData.get("duration", -1))
                if duration > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=actionChannelDelete,
                                        functionArgs=[channels,
                                                      str(channelData.get("channel_delete_reason", ""))],
                                        **defaultArguments)
        elif guildToDo == "channel_delete":
            for channelData in listData:
                deletedChannels: list = []
                for channel in utils.getChannels(channelData, guild):
                    res: bool = await utils.deleteChannel(channel, reason=str(channelData.get("reason", "")))
                    if res:
                        deletedChannels.append(channel)
                duration: int = int(channelData.get("duration", -1))
                if duration > 0:
                    defaultArguments["duration"] = duration
                    startBackgroundTask(function=actionChannelCreate,
                                        functionArgs=[deletedChannels,
                                                      str(channelData.get("channel_create_reason", ""))],
                                        **defaultArguments)
        elif guildToDo == "channel_edit":
            for channelData in listData:
                pass


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
