import discord

from cogs.ext.imports import *


async def createSticker(data: dict, guild: discord.Guild) -> discord.GuildSticker:
    return await guild.create_sticker(name=str(data.get("name", "StickerName")), description=str(data.get("name", "")),
                                      emoji=str(data.get("emoji", "")),
                                      file=File(filename=data.get("file_name"), fp=data.get("fp")),
                                      reason=str(data.get("reason", "")))


async def deleteSticker(sticker: discord.GuildSticker, reason: str = ""):
    await sticker.delete(reason=reason)


async def editSticker(data: dict, sticker: discord.GuildSticker):
    await sticker.edit(name=str(data.get("new_name", sticker.name)),
                       description=str(data.get("description", sticker.description)),
                       emoji=str(data.get("emoji", sticker.emoji)),
                       reason=str(data.get("reason", "")))


def getStickerSearchData(stickerData) -> tuple:
    stickerIds = stickerData.get("sticker_id")
    stickerNames = stickerData.get("sticker_name")
    if not isinstance(stickerIds, list):
        stickerIds = [stickerIds] if isinstance(stickerIds, int) else []
    if not isinstance(stickerNames, list):
        stickerNames = [stickerNames] if isinstance(stickerNames, str) else []
    return stickerIds, stickerNames


async def getStickers(data: dict, guild: discord.Guild) -> List[discord.GuildSticker]:
    stickers = await guild.fetch_stickers()
    stickerIds, stickerNames = getStickerSearchData(data)
    res = []
    for sticker in stickers:
        if sticker.name in stickerNames or sticker.id in stickerIds:
            res.append(sticker)
    return res


def getStickerData(sticker: discord.GuildSticker) -> dict:
    data: dict = dict()
    data["name"] = sticker.name
    data["id"] = sticker.id
    data["emoji"] = sticker.emoji
    data["description"] = sticker.description
    data["created_at"] = sticker.created_at
    data["url"] = sticker.url
    data["filename"] = ""
    data["fp"] = rq.get(sticker.url).content
    data["format"] = sticker.format
    data["guild_id"] = sticker.guild_id
    return data



