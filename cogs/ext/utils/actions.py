from __future__ import annotations

import asyncio
import threading
from datetime import datetime
from typing import List, Dict

import discord
from discord import Member
from discord.ext import commands
import cogs.ext.utils.utils as utils
import cogs.ext.utils.messages as messages


async def handleActionMessages(interaction: discord.Interaction, messages_names: list):
    for msg in messages_names:
        await messages.handleMessage(interaction.client, interaction,
                                     usePlaceholders(msg, interaction), DMUser=interaction.user)


async def handleCogCommandExecution(cog: commands.Cog, interaction: discord.Interaction,
                                    commandName: str,
                                    command: discord.app_commands.commands.ContextMenu, finalArgs: list):
    for co in cog.get_app_commands():
        if co.name == commandName:
            try:
                await command.callback(cog, interaction, *finalArgs)
            except Exception as e:
                await messages.handleErrors(interaction.client, interaction, commandName, e)
            break


def usePlaceholders(msg: str, interaction: discord.Interaction) -> str:
    msg = msg.replace("@user.id", str(interaction.user.id))
    msg = msg.replace("@user.name", str(interaction.user.name))
    msg = msg.replace("@user.avatar.is_animated", str(interaction.user.avatar.is_animated()))

    msg = msg.replace("@channel.id", str(interaction.channel.id))
    msg = msg.replace("@channel.name", str(interaction.channel.name))
    msg = msg.replace("@channel.type", str(interaction.channel.type.name))

    botUser: discord.ClientUser | None = interaction.client
    if botUser is not None:
        msg = msg.replace("@bot.id", str(botUser.id))
        msg = msg.replace("@bot.name", str(botUser.name))
        msg = msg.replace("@bot.latency", str(interaction.client.latency))

    msg = msg.replace("@guild.id", str(interaction.guild.id))
    msg = msg.replace("@guild.name", str(interaction.guild.name))

    for roleManager in utils.configManager.getRoleManagements():
        botRoleManager: str = "@bot." + roleManager
        userRoleManager: str = "@user." + roleManager
        guildRoleManager: str = "@guild." + roleManager
        if botRoleManager in msg and botUser is not None:
            botMember: Member | None = interaction.guild.get_member(botUser.id)
            if botMember is not None and checkIf(roleManager, utils.getRoleIdFromRoles(botMember.roles.copy()).copy()):
                msg = msg.replace(botRoleManager, roleManager)

        elif userRoleManager in msg:
            if checkIf(roleManager, utils.getRoleIdFromRoles(interaction.user.roles.copy()).copy()):
                msg = msg.replace(userRoleManager, roleManager)

        elif guildRoleManager in msg:
            if checkIf(roleManager, utils.getRoleIdFromRoles(list(interaction.guild.roles).copy()).copy()):
                msg = msg.replace(userRoleManager, roleManager)
    return msg


def checkIf(roleManager: str, hasRoles: list) -> bool:
    return (utils.allRolesContains(utils.configManager.getAllRolesIDByRoleManager(roleManager).copy(), hasRoles) or
            utils.anyRolesContains(hasRoles, utils.configManager.getAnyRolesIDByRoleManager(roleManager).copy()))


async def handleActionCommands(interaction: discord.Interaction, commandsData: dict):
    for command in commandsData.keys():
        comm: discord.app_commands.commands.ContextMenu | None = interaction.client.tree.get_command(command)
        if comm is not None:
            final_args = []
            for arg in commandsData.get(command):
                final_args.append(usePlaceholders(arg, interaction))

            for name, file_name in utils.configManager.getCogData().items():
                cog: commands.Cog = interaction.client.get_cog(name)
                executed = False
                for cogCommand in cog.get_app_commands():
                    if cogCommand.name == comm.name:
                        try:
                            await interaction.client.load_extension(f"cogs.{file_name}")
                        except commands.ExtensionAlreadyLoaded:
                            await handleCogCommandExecution(cog, interaction, command, comm, final_args)
                        executed = True
                        break
                if executed:
                    break


async def handleUser(interaction: discord.Interaction, userData: dict):
    for userDo in userData.keys():
        userDoData: dict = userData.get(userDo, {})
        if isinstance(userDoData, dict):
            continue
        duration: int = int(userDoData.get("duration", -1))
        loop = asyncio.get_running_loop()
        user = interaction.user
        users: list = utils.getUsers(userDoData, interaction.guild)
        roles: list = utils.getRoles(userDoData, interaction.guild)
        reason = str(userDoData.get("reason", ""))
        if userDo == "ban":
            usersBanned: list = []
            if bool(userDoData.get("interact_both", True)):
                res: bool = await utils.banUser(user, reason=reason)
                if res:
                    usersBanned.append(user)
            for resUser in users:
                res: bool = await utils.banUser(resUser, reason=reason)
                if res:
                    usersBanned.append(resUser)
            if duration > 0:
                async def wait(duration2: int, unbanReason: str, userD: discord.Member):
                    try:
                        await asyncio.sleep(duration2)
                        await utils.unbanUser(userD, reason=unbanReason)
                    except Exception:
                        pass

                threading.Thread(target=utils.separateThread, args=(loop, wait, duration,
                                                                    str(userDoData.get("unban_reason", "")),
                                                                    usersBanned), daemon=True).start()
        elif userDo == "unban":
            usersUnbanned: list = []
            if bool(userDoData.get("interact_both", True)):
                res: bool = await utils.unbanUser(user, reason=reason)
                if res:
                    usersUnbanned.append(user)
            for resUser in users:
                res: bool = await utils.unbanUser(resUser, reason=reason)
                if res:
                    usersUnbanned.append(resUser)

            if duration > 0:
                async def wait(duration2: int, members: List[discord.Member], reason: str):
                    try:
                        await asyncio.sleep(duration2)
                        for member in members:
                            await utils.banUser(member, reason=reason)
                    except Exception:
                        pass

                threading.Thread(target=utils.separateThread, args=(loop, wait, duration, usersUnbanned,
                                                                    str(userDoData.get("ban_reason", ""))),
                                 daemon=True).start()
        elif userDo == "kick":
            if bool(userDoData.get("interact_both", True)):
                await utils.kickUser(user, reason=reason)
            for resUser in users:
                await utils.kickUser(resUser, reason=reason)
        elif userDo == "role_add":
            roleAdded: dict = dict()
            for role in roles:
                roleAdded[role] = []
                if bool(userDoData.get("interact_both", True)):
                    res: bool = await utils.addRole(user, role, reason=reason)
                    if res:
                        roleAdded[role].append(user)
                for resUser in users:
                    res: bool = await utils.addRole(resUser, role, reason=reason)
                    if res:
                        roleAdded[role].append(resUser)
            if duration > 0:
                async def wait(duration2: int, reason1: str, addedRoles: Dict[discord.Role, List[discord.Member]]):
                    try:
                        await asyncio.sleep(duration2)
                        for addedRole, addedMembers in addedRoles.items():
                            for mem in addedMembers:
                                await utils.removeRole(mem, addedRole, reason=reason1)
                    except Exception:
                        pass

                threading.Thread(target=utils.separateThread, args=(loop, wait, duration,
                                                                    str(userDoData.get("role_remove_reason", "")),
                                                                    roleAdded),
                                 daemon=True).start()
        elif userDo == "role_remove":
            roleRemoved: dict = dict()
            for role in roles:
                roleRemoved[role] = []
                if bool(userDoData.get("interact_both", True)):
                    res: bool = await utils.removeRole(user, role, reason=reason)
                    if res:
                        roleRemoved[role].append(user)
                for resUser in users:
                    res: bool = await utils.removeRole(resUser, role, reason=reason)
                    if res:
                        roleRemoved[role].append(resUser)
            if duration > 0:
                async def wait(duration2: int, reason1: str, addedRoles: Dict[discord.Role, List[discord.Member]]):
                    try:
                        await asyncio.sleep(duration2)
                        for addedRole, addedMembers in addedRoles.items():
                            for mem in addedMembers:
                                await utils.addRole(mem, addedRole, reason=reason1)
                    except Exception:
                        pass

                threading.Thread(target=utils.separateThread, args=(loop, wait, duration,
                                                                    str(userDoData.get("role_add_reason", "")),
                                                                    roleRemoved),
                                 daemon=True).start()
        elif userDo == "timeout":
            timeoutedMembers: list = []
            strptime = datetime.strptime(reason, "YYYY-MM-DDTHH:MM:SS")
            if bool(userDoData.get("interact_both", True)):
                res: bool = await utils.timeoutUser(user, strptime, reason=reason)
                if res:
                    timeoutedMembers.append(user)
            for resUser in users:
                res: bool = await utils.timeoutUser(resUser, strptime, reason=reason)
                if res:
                    timeoutedMembers.append(resUser)
            if duration > 0:
                async def wait(duration2: int, reason1: str, timeoutMembers: List[discord.Member]):
                    try:
                        await asyncio.sleep(duration2)
                        for mem in timeoutMembers:
                            await utils.removeTimeoutUser(mem, reason=reason1)
                    except Exception:
                        pass

                threading.Thread(target=utils.separateThread, args=(loop, wait, duration,
                                                                    str(userDoData.get("timeout_remove_reason", "")),
                                                                    timeoutedMembers), daemon=True).start()
        elif userDo == "deafen":
            deafenMembers: list = []
            if bool(userDoData.get("interact_both", True)):
                res: bool = await utils.userDeafen(user, True, reason=reason)
                if res:
                    deafenMembers.append(user)
            for resUser in users:
                res: bool = await utils.userDeafen(user, True, reason=reason)
                if res:
                    deafenMembers.append(resUser)

            if duration > 0:
                async def wait(duration2: int, reason1: str, deafenMembers1: List[discord.Member]):
                    try:
                        await asyncio.sleep(duration2)
                        for mem in deafenMembers1:
                            await utils.userDeafen(mem, False, reason=reason1)
                    except Exception:
                        pass

                threading.Thread(target=utils.separateThread, args=(loop, wait, duration,
                                                                    str(userDoData.get("deafen_remove_reason", "")),
                                                                    deafenMembers), daemon=True).start()
        elif userDo == "deafen_remove":
            removeDeafenMembers: list = []
            if bool(userDoData.get("interact_both", True)):
                res: bool = await utils.userDeafen(user, False, reason=reason)
                if res:
                    removeDeafenMembers.append(user)
            for resUser in users:
                res: bool = await utils.userDeafen(user, False, reason=reason)
                if res:
                    removeDeafenMembers.append(resUser)

            if duration > 0:
                async def wait(duration2: int, reason1: str, removeDeafenMembers1: List[discord.Member]):
                    try:
                        await asyncio.sleep(duration2)
                        for mem in removeDeafenMembers1:
                            await utils.userDeafen(mem, True, reason=reason1)
                    except Exception:
                        pass

                threading.Thread(target=utils.separateThread, args=(loop, wait, duration,
                                                                    str(userDoData.get("deafen_reason", "")),
                                                                    removeDeafenMembers), daemon=True).start()
        elif userDo == "mute":
            removeMutedMembers: list = []
            if bool(userDoData.get("interact_both", True)):
                res: bool = await utils.userMute(user, True, reason=reason)
                if res:
                    removeMutedMembers.append(user)
            for resUser in users:
                res: bool = await utils.userMute(user, True, reason=reason)
                if res:
                    removeMutedMembers.append(resUser)

            if duration > 0:
                async def wait(duration2: int, reason1: str, mutedMembers1: List[discord.Member]):
                    try:
                        await asyncio.sleep(duration2)
                        for mem in mutedMembers1:
                            await utils.userMute(mem, False, reason=reason1)
                    except Exception:
                        pass

                threading.Thread(target=utils.separateThread, args=(loop, wait, duration,
                                                                    str(userDoData.get("mute_remove_reason", "")),
                                                                    removeMutedMembers), daemon=True).start()
        elif userDo == "mute_remove":
            removeMutedMembers: list = []
            if bool(userDoData.get("interact_both", True)):
                res: bool = await utils.userMute(user, False, reason=reason)
                if res:
                    removeMutedMembers.append(user)
            for resUser in users:
                res: bool = await utils.userMute(user, False, reason=reason)
                if res:
                    removeMutedMembers.append(resUser)

            if duration > 0:
                async def wait(duration2: int, reason1: str, removeMutedMembers1: List[discord.Member]):
                    try:
                        await asyncio.sleep(duration2)
                        for mem in removeMutedMembers1:
                            await utils.userMute(mem, True, reason=reason1)
                    except Exception:
                        pass

                threading.Thread(target=utils.separateThread, args=(loop, wait, duration,
                                                                    str(userDoData.get("mute_reason", "")),
                                                                    removeMutedMembers), daemon=True).start()


async def handleGuild(interaction: discord.Interaction, guildData: dict):
    for guildToDo in guildData.keys():
        loop = asyncio.get_running_loop()
        # TODO finish this
        guild = interaction.guild
        listData = guildData.get(guildToDo, [])
        if guildToDo == "role_create":
            if not isinstance(listData, list):
                listData = []
            for rolesToCreate in listData:
                if not isinstance(rolesToCreate, dict):
                    continue
                duration: int = int(rolesToCreate.get("duration", -1))
                role = await utils.createRoleWithDisplayIcon(rolesToCreate, guild)
                if role is None:
                    role = await utils.createRoleNoDisplayIcon(rolesToCreate, guild)
                    if role is None:
                        continue

                if duration > 0:
                    async def wait(duration2: int, roleToDelete: discord.Role, reason: str):
                        try:
                            await asyncio.sleep(duration2)
                            await utils.deleteRole(roleToDelete, reason=reason)
                        except Exception:
                            pass

                    threading.Thread(target=utils.separateThread, args=(loop, wait, duration, role,
                                                                        rolesToCreate.get("delete_reason", "")),
                                     daemon=True).start()
        elif guildToDo == "role_delete":
            if not isinstance(listData, list):
                listData = []
            for rolesToDelete in listData:
                if not isinstance(rolesToDelete, dict):
                    continue
                duration: int = int(rolesToDelete.get("duration", -1))
                roles: list = []
                for selectedRole in utils.getRoles(rolesToDelete, interaction.guild):
                    res: bool = await utils.deleteRole(selectedRole, guild)
                    if res:
                        roles.append(selectedRole)
                if duration > 0:
                    async def wait(duration2: int, guildD: discord.Guild, rolesToCreate2: List[discord.Role],
                                   reason: str, give_back_roles_to_users: bool, give_back_reason: str):
                        try:
                            await asyncio.sleep(duration2)
                            for roleToCreate in rolesToCreate2:
                                roleData: dict = utils.getRoleData(roleToCreate)
                                roleData["reason"] = reason
                                if not give_back_roles_to_users:
                                    roleData.pop("users")
                                roleCreated = await utils.createRoleWithDisplayIcon(roleData, guildD)
                                if roleCreated is None:
                                    roleCreated = await utils.createRoleNoDisplayIcon(roleData, guildD)
                                    if roleCreated is None:
                                        continue
                                if "users" not in roleData.keys() or len(roleData.get("users", [])) == 0:
                                    continue
                                for userId in roleData.get("users", []):
                                    member: discord.Member | None = utils.getMemberGuild(guildD, userId)
                                    if member is None:
                                        continue
                                    await utils.addRole(member, roleCreated, reason=give_back_reason)
                        except Exception:
                            pass

                    threading.Thread(target=utils.separateThread, args=(loop, wait, duration, guild,
                                                                        roles,
                                                                        str(rolesToDelete.get("create_reason", "")),
                                                                        bool(rolesToDelete.get(
                                                                            "give_back_roles_to_users", False)),
                                                                        str(rolesToDelete.get("give_back_reason", ""))),
                                     daemon=True).start()
        elif guildToDo == "role_edit":
            if not isinstance(listData, list):
                listData = []
            for rolesToEdit in listData:
                if not isinstance(rolesToEdit, dict):
                    continue
                roles: List[discord.Role] = utils.getRoles(rolesToEdit, guild)
                edited: dict[discord.Role, dict] = dict()
                for role in roles:
                    prevStatus: dict = utils.getRoleData(role)
                    res: bool = await utils.editRole(rolesToEdit, role)
                    if res:
                        edited[role] = prevStatus
                duration: int = int(rolesToEdit.get("duration", -1))
                if duration > 0:
                    async def wait(duration2: int, guildD: discord.Guild, editedRoles: dict[discord.Role, dict],
                                   editReason: str):
                        try:
                            await asyncio.sleep(duration2)
                            for editedRole, prevData in editedRoles.items():
                                prevData["reason"] = editReason
                                prevData["new_name"] = prevData.pop("name")
                                await utils.editRole(prevData, editedRole)
                        except Exception:
                            pass

                    threading.Thread(target=utils.separateThread, args=(loop, wait, duration, guild,
                                                                        edited,
                                                                        str(rolesToEdit.get("edit_reason", ""))),
                                     daemon=True).start()
        elif guildToDo == "overview":
            overviewData: dict = dict(guildData.get(guildToDo, {}))
            fullPrevData: dict = utils.getGuildData(guild)
            res: bool = await utils.editGuild(overviewData, guild)
            prevData: dict = dict()
            if not res:
                continue
            for key in overviewData.keys():
                if key not in fullPrevData.keys():
                    continue
                prevData[key] = fullPrevData.get(key)
            duration: int = int(overviewData.get("duration", -1))
            if duration > 0:
                async def wait(duration2: int, guildD: discord.Guild, prevDataGuild: dict, reason: str):
                    try:
                        await asyncio.sleep(duration2)
                        await utils.editGuild(prevDataGuild, guildD, reason=reason)
                    except Exception:
                        pass

                threading.Thread(target=utils.separateThread, args=(loop, wait, duration, guild, prevData,
                                                                    str(overviewData.get("reason", ""))),
                                 daemon=True).start()
        elif guildToDo == "category_create":
            if not isinstance(listData, list):
                listData = []
            for categoryData in listData:
                if not isinstance(categoryData, dict):
                    continue
                category: discord.CategoryChannel | None = await utils.createCategory(categoryData, guild)
                if category is None:
                    continue
                duration: int = int(categoryData.get("duration", -1))
                if duration > 0:
                    async def wait(duration2: int, categoryToDelete: discord.CategoryChannel, deleteReason: str):
                        try:
                            await asyncio.sleep(duration2)
                            await utils.deleteCategory(categoryToDelete, deleteReason)
                        except Exception:
                            pass

                    threading.Thread(target=utils.separateThread, args=(loop, wait, duration, category,
                                                                        str(categoryData.get("category_delete_reason",
                                                                                             ""))),
                                     daemon=True).start()
        elif guildToDo == "category_delete":
            if not isinstance(listData, list):
                listData = []
            for categoryData in listData:
                if not isinstance(categoryData, dict):
                    continue
                deletedCategories: List[discord.CategoryChannel] = []
                for category in utils.getCategories(categoryData, guild):
                    res: bool = await utils.deleteCategory(category, reason=str(categoryData.get("reason", "")))
                    if res:
                        deletedCategories.append(category)

                duration: int = int(categoryData.get("duration", -1))
                if duration > 0:
                    async def wait(duration2: int, guildD: discord.Guild,
                                   categoriesToCreate: List[discord.CategoryChannel], createReason: str):
                        try:
                            await asyncio.sleep(duration2)
                            for categories in categoriesToCreate:
                                catData: dict = utils.getCategoryData(categories)
                                catData["reason"] = createReason
                                await utils.createCategory(catData, guildD)
                        except Exception:
                            pass

                    threading.Thread(target=utils.separateThread, args=(loop, wait, duration, guild, deletedCategories,
                                                                        str(categoryData.get("category_create_reason",
                                                                                             ""))),
                                     daemon=True).start()
        elif guildToDo == "category_edit":
            if not isinstance(listData, list):
                listData = []
            for categoryData in listData:
                if not isinstance(categoryData, dict):
                    continue
                editedCategories: Dict[discord.CategoryChannel, dict] = dict()
                for category in utils.getCategories(categoryData, guild):
                    categoryPrevData: dict = utils.getCategoryData(category)
                    res: bool = await utils.editCategory(category, categoryData)
                    if res:
                        editedCategories[category] = categoryPrevData

                duration: int = int(categoryData.get("duration", -1))
                if duration > 0:
                    async def wait(duration2: int, categoriesToEdit: Dict[discord.CategoryChannel, dict],
                                   editReason: str):
                        try:
                            await asyncio.sleep(duration2)
                            for categories, prevData in categoriesToEdit.items():
                                prevData["reason"] = editReason
                                prevData["new_name"] = prevData.pop("name")
                                await utils.editCategory(categories, prevData)
                        except Exception:
                            pass

                    threading.Thread(target=utils.separateThread, args=(loop, wait, duration, editedCategories,
                                                                        str(categoryData.get("category_edit_reason",
                                                                                             ""))),
                                     daemon=True).start()
        elif guildToDo == "channel_create":
            if not isinstance(listData, list):
                listData = []
            for channelData in listData:
                if not isinstance(channelData, dict):
                    continue
                channels: list = await utils.createChannel(channelData, guild)
                if len(channels) == 0:
                    continue
                duration: int = int(channelData.get("duration", -1))
                if duration > 0:
                    async def wait(duration2: int, channelsToDelete: list, deleteReason: str):
                        try:
                            await asyncio.sleep(duration2)
                            for channel in channelsToDelete:
                                await utils.deleteChannel(channel, deleteReason)
                        except Exception:
                            pass

                    threading.Thread(target=utils.separateThread, args=(loop, wait, duration, channels,
                                                                        str(channelData.get("channel_delete_reason",
                                                                                            ""))),
                                     daemon=True).start()
        elif guildToDo == "channel_delete":
            if not isinstance(listData, list):
                listData = []
            for channelData in listData:
                if not isinstance(channelData, dict):
                    continue
                deletedChannels: list = []
                for channel in utils.getChannels(channelData, guild):
                    res: bool = await utils.deleteChannel(channel, reason=str(channelData.get("reason", "")))
                    if res:
                        deletedChannels.append(channel)
                duration: int = int(channelData.get("duration", -1))
                if duration > 0:
                    async def wait(duration2: int, channelsToCreate: list, createReason: str):
                        try:
                            await asyncio.sleep(duration2)
                            for channel in channelsToCreate:
                                data: dict = utils.getChannelData(channel)
                                data["reason"] = createReason
                                try:
                                    await utils.createChannel(data, channel.guild)
                                except Exception:
                                    continue
                        except Exception:
                            pass

                    threading.Thread(target=utils.separateThread, args=(loop, wait, duration, deletedChannels,
                                                                        str(channelData.get("channel_create_reason",
                                                                                            ""))),
                                     daemon=True).start()



async def handleAllActions(actionData: dict, interaction: discord.Interaction):
    for action in actionData.keys():
        for doing in actionData.get(action).keys():
            if doing == "messages":
                await handleActionMessages(interaction, list(actionData.get(action, {}).get(doing, [])).copy())

            elif doing == "commands":
                await handleActionCommands(interaction, dict(actionData.get(action, {}).get(doing, {})).copy())

            elif doing == "user":
                await handleUser(interaction, dict(actionData.get(action, {}).get(doing, {})).copy())

            elif doing == "guild":
                await handleGuild(interaction, dict(actionData.get(action, {}).get(doing, {})).copy())
