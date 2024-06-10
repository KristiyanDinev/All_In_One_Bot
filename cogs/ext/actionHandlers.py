from typing import List, Dict

import discord

from cogs.ext.imports import *
from cogs.ext.utils import utils


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


async def actionCreateStickers(stickers: List[discord.GuildSticker], reason: str):
    for sticker in stickers:
        data: dict = utils.getStickerData(sticker)
        data["reason"] = reason
        await utils.createSticker(data, sticker.guild)


async def actionEditStickers(stickers: Dict[discord.GuildSticker, Dict], reason: str):
    for sticker, prevData in stickers.items():
        prevData["reason"] = reason
        prevData["new_name"] = prevData.pop("name")
        await utils.editSticker(prevData, sticker)

