from cogs.ext.imports import *


async def createEmoji(data: dict, guild: discord.Guild) -> discord.Emoji:
    roles = getRoles(data.get("roles"), guild)
    if len(roles) > 0:
        return await guild.create_custom_emoji(name=str(data.get("name", "EmojiName")), image=data.get("image"),
                                               reason=str(data.get("reason", "")), roles=roles)
    else:
        return await guild.create_custom_emoji(name=str(data.get("name", "EmojiName")), image=data.get("image"),
                                               reason=str(data.get("reason", "")))


def getEmojiSearchData(emojiData) -> tuple:
    emojiIds = emojiData.get("emoji_id")
    emojiNames = emojiData.get("emoji_name")
    if not isinstance(emojiIds, list):
        emojiIds = [emojiIds] if isinstance(emojiIds, int) else []
    if not isinstance(emojiNames, list):
        emojiNames = [emojiNames] if isinstance(emojiNames, str) else []
    return emojiIds, emojiNames


async def getEmojis(data: dict, guild: discord.Guild) -> List[discord.Emoji]:
    emojis = await guild.fetch_emojis()
    emojiIds, emojiNames = getEmojiSearchData(data)
    res = []
    for emoji in emojis:
        if emoji.name in emojiNames or emoji.id in emojiIds:
            res.append(emoji)
    return res


async def deleteEmoji(emoji: discord.Emoji, reason: str = ""):
    await emoji.delete(reason=reason)


async def editEmoji(data: dict, emoji: discord.Emoji):
    roles = getRoles(data.get("roles"), emoji.guild)
    if len(roles) > 0:
        await emoji.edit(roles=roles, reason=str(data.get("reason", "")))
    if "name" in data.keys():
        await emoji.edit(name=str(data.get("new_name", emoji.name)), reason=str(data.get("reason", "")))


def getEmojiData(emoji: discord.Emoji) -> dict:
    data: dict = dict()
    data["id"] = emoji.id
    data["name"] = emoji.name
    data["url"] = emoji.url
    data["image"] = rq.get(emoji.url).content
    data["created_at"] = emoji.created_at
    data["roles"] = emoji.roles
    data["animated"] = emoji.animated
    data["is_usable"] = emoji.is_usable()
    data["available"] = emoji.available
    data["guild_id"] = emoji.guild_id
    return data

