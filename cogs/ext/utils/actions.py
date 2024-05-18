from __future__ import annotations

import asyncio
import threading
from datetime import datetime

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
        userDoData: dict = dict(userData.get(userDo, {}))
        duration: int = int(userDoData.get("duration", -1))
        loop = asyncio.get_running_loop()
        if userDo == "ban":
            try:
                await interaction.user.ban(reason=str(userDoData.get("ban_reason", "")))

                if duration > 0:
                    async def wait(duration2: int, reason: str, user: discord.Member):
                        try:
                            await asyncio.sleep(duration2)
                            await user.unban(reason=reason)
                        except Exception:
                            pass

                    threading.Thread(target=utils.separateThread, args=(loop, wait, duration,
                                                                        str(userDoData.get("unban_reason", "")),
                                                                        interaction.user), daemon=True).start()
            except Exception as e:
                await messages.handleErrors(interaction.client, interaction, userDo, e)

        elif userDo == "unban":
            try:
                member: discord.Member | None = utils.getMember(interaction,
                                                                utils.getMemberIdFromMention(
                                                                    str(userDoData.get("id", "0"))))
                if member is not None:
                    await member.unban(reason=str(userDoData.get("unban_reason", "")))
                    duration: int = int(userDoData.get("duration", -1))

                    if duration > 0:
                        async def wait(duration2: int, member2: discord.Member):
                            try:
                                await asyncio.sleep(duration2)
                                await member2.ban(reason=str(userDoData.get("ban_reason", "")))
                            except Exception:
                                pass

                        threading.Thread(target=utils.separateThread, args=(loop, wait, duration, member),
                                         daemon=True).start()

            except Exception as e:
                await messages.handleErrors(interaction.client, interaction, userDo, e)

        elif userDo == "kick":
            try:
                await interaction.user.kick(reason=str(userDoData.get("kick_reason", "")))
            except Exception as e:
                await messages.handleErrors(interaction.client, interaction, userDo, e)

        elif userDo == "role_add":
            try:
                role: discord.Role | None = utils.getRole(interaction,
                                                          utils.getRoleIdFromMention(
                                                              str(userDoData.get("id", 0))))
                if role is not None:
                    await interaction.user.add_roles(role, reason=str(userDoData.get("reason", "")))

                    if duration > 0:
                        async def wait(duration2: int, reason: str, user: discord.Member, userRole: discord.Role):
                            try:
                                await asyncio.sleep(duration2)
                                await user.remove_roles(userRole, reason=reason)
                            except Exception:
                                pass

                        threading.Thread(target=utils.separateThread, args=(loop, wait, duration,
                                                                            str(userDoData.get("role_remove_reason",
                                                                                                "")),
                                                                            interaction.user, role),
                                         daemon=True).start()
            except Exception as e:
                await messages.handleErrors(interaction.client, interaction, userDo, e)

        elif userDo == "role_remove":
            try:
                role: discord.Role | None = utils.getRole(interaction,
                                                          utils.getRoleIdFromMention(
                                                              str(userDoData.get("id", 0))))
                if role is not None:
                    await interaction.user.remove_roles(role, reason=str(userDoData.get("reason", "")))

                    if duration > 0:
                        async def wait(duration2: int, reason: str, user: discord.Member, userRole: discord.Role):
                            try:
                                await asyncio.sleep(duration2)
                                await user.add_roles(userRole, reason=reason)
                            except Exception:
                                pass

                        threading.Thread(target=utils.separateThread, args=(loop, wait, duration,
                                                                            str(userDoData.get("role_add_reason",
                                                                                                "")),
                                                                            interaction.user, role),
                                         daemon=True).start()
            except Exception as e:
                await messages.handleErrors(interaction.client, interaction, userDo, e)

        elif userDo == "timeout":
            try:
                await interaction.user.timeout(datetime.strptime(str(userDoData.get("reason", "")),
                                                                 "YYYY-MM-DDTHH:MM:SS"),
                                               reason=str(userDoData.get("timeout_reason", "")))
                duration: int = int(userDoData.get("duration", -1))

                if duration > 0:
                    async def wait(duration2: int, reason: str, user: discord.Member):
                        try:
                            await asyncio.sleep(duration2)
                            await user.edit(timed_out_until=None, reason=reason)
                        except Exception:
                            pass

                    threading.Thread(target=utils.separateThread, args=(loop, wait, duration,
                                                                        str(userDoData.get("untimeout_unban_reason",
                                                                                            "")),
                                                                        interaction.user), daemon=True).start()
            except Exception as e:
                await messages.handleErrors(interaction.client, interaction, userDo, e)

        elif userDo == "deafen":
            try:
                await interaction.user.edit(deafen=True, reason=str(userDoData.get("deafen_reason", "")))
                duration: int = int(userDoData.get("duration", -1))

                if duration > 0:
                    async def wait(duration2: int, reason: str, user: discord.Member):
                        try:
                            await asyncio.sleep(duration2)
                            await user.edit(deafen=False, reason=reason)
                        except Exception:
                            pass

                    threading.Thread(target=utils.separateThread, args=(loop, wait, duration,
                                                                        str(userDoData.get("undeafen_reason", "")),
                                                                        interaction.user), daemon=True).start()
            except Exception as e:
                await messages.handleErrors(interaction.client, interaction, userDo, e)

        elif userDo == "undeafen":
            try:
                await interaction.user.edit(deafen=False, reason=str(userDoData.get("deafen_reason", "")))
                duration: int = int(userDoData.get("duration", -1))

                if duration > 0:
                    async def wait(duration2: int, reason: str, user: discord.Member):
                        try:
                            await asyncio.sleep(duration2)
                            await user.edit(deafen=True, reason=reason)
                        except Exception:
                            pass

                    threading.Thread(target=utils.separateThread, args=(loop, wait, duration,
                                                                        str(userDoData.get("undeafen_reason", "")),
                                                                        interaction.user), daemon=True).start()
            except Exception as e:
                await messages.handleErrors(interaction.client, interaction, userDo, e)

        elif userDo == "mute":
            try:
                await interaction.user.edit(mute=True, reason=str(userDoData.get("mute_reason", "")))
                duration: int = int(userDoData.get("duration", -1))

                if duration > 0:
                    async def wait(duration2: int, reason: str, user: discord.Member):
                        try:
                            await asyncio.sleep(duration2)
                            await user.edit(mute=False, reason=reason)
                        except Exception:
                            pass

                    threading.Thread(target=utils.separateThread, args=(loop, wait, duration,
                                                                        str(userDoData.get("unmute_reason", "")),
                                                                        interaction.user), daemon=True).start()
            except Exception as e:
                await messages.handleErrors(interaction.client, interaction, userDo, e)

        elif userDo == "unmute":
            try:
                await interaction.user.edit(mute=False, reason=str(userDoData.get("mute_reason", "")))
                duration: int = int(userDoData.get("duration", -1))

                if duration > 0:
                    async def wait(duration2: int, reason: str, user: discord.Member):
                        try:
                            await asyncio.sleep(duration2)
                            await user.edit(mute=True, reason=reason)
                        except Exception:
                            pass

                    threading.Thread(target=utils.separateThread, args=(loop, wait, duration,
                                                                        str(userDoData.get("unmute_reason", "")),
                                                                        interaction.user), daemon=True).start()
            except Exception as e:
                await messages.handleErrors(interaction.client, interaction, userDo, e)

async def handleGuild(interaction: discord.Interaction, guildData: dict):
    for roleDo in guildData.keys():
        guildDoData: dict = dict(guildData.get(roleDo, {}))
        duration: int = int(guildDoData.get("duration", -1))
        loop = asyncio.get_running_loop()
        # TODO finish this
        if roleDo == "role_create":
            try:
                color: str = guildDoData.get("color", "")
                role: discord.Role = await interaction.guild.create_role(reason=guildDoData.get("reason", ""),
                                                    name=guildDoData.get("name", "No Name Given"),
                                                    display_icon=guildDoData.get("display_icon", "No Name Given"),
                                                    color=discord.Colour.random()
                                                    if color == "random" or len(color) == 0 else
                                                    discord.Color.from_str(color),
                                                    mentionable=bool(guildDoData.get("mentionable", True)),
                                                    hoist=bool(guildDoData.get("hoist", True)),
                                                    permissions=discord.Permissions(**
                                                        dict(guildDoData.get("permissions", {}))))

                if duration > 0:
                    async def wait(duration2: int, bot: commands.Bot, roleToDelete: discord.Role):
                        try:
                            await asyncio.sleep(duration2)
                            await bot.delete_role(roleToDelete.guild, roleToDelete)
                        except Exception:
                            pass

                    threading.Thread(target=utils.separateThread, args=(loop, wait, duration,
                                                                        interaction.client, role), daemon=True).start()
            except Exception as e:
                await messages.handleErrors(interaction.client, interaction, roleDo, e)


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
