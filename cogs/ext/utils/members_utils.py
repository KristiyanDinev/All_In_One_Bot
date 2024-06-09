from cogs.ext.imports import *


def getMemberGuild(guild: discord.Guild, memberId: int) -> discord.Member | None:
    if memberId == 0:
        return None
    return guild.get_member(memberId)


def getMemberIdFromMention(memberMention: str) -> int:
    try:
        return int(memberMention.replace("<@", "")[:-1]) if "<@" in memberMention else int(memberMention)
    except Exception:
        return 0


async def giveRoleToUser(member: discord.Member, role: discord.Role, reason: str = ""):
    await member.add_roles(role, reason=reason)


async def removeRoleToUser(member: discord.Member, role: discord.Role, reason: str = ""):
    await member.remove_roles(role, reason=reason)


async def banUser(member: discord.Member, reason: str = ""):
    await member.ban(reason=reason)


async def unbanUser(member: discord.Member, reason: str = ""):
    await member.unban(reason=reason)


async def kickUser(member: discord.Member, reason: str = ""):
    await member.kick(reason=reason)


async def addRole(member: discord.Member, role: discord.Role, reason: str = ""):
    await member.add_roles(role, reason=reason)


async def removeRole(member: discord.Member, role: discord.Role, reason: str = ""):
    await member.remove_roles(role, reason=reason)


async def timeoutUser(member: discord.Member, datetime_zone, reason: str = ""):
    await member.timeout(datetime_zone, reason=reason)


async def removeUserTimeout(member: discord.Member, reason: str = ""):
    await member.edit(timed_out_until=None, reason=reason)


async def userDeafen(member: discord.Member, status: bool, reason: str = ""):
    await member.edit(deafen=status, reason=reason)


async def userMute(member: discord.Member, status: bool, reason: str = ""):
    await member.edit(mute=status, reason=reason)


def getBannedMembers(userData: dict, guild: discord.Guild) -> List[discord.Member]:
    userIds, userNames = getUserSearchData(userData)
    members = []
    async for banned in guild.bans():
        user = banned[0]
        if user is not None and (user.id in userIds or user.name in userNames):
            members.append(user)
    return members


def getUserSearchData(userData) -> tuple:
    userIds = userData.get("user_id")
    userNames = userData.get("user_name")
    if not isinstance(userIds, list):
        userIds = [userIds] if isinstance(userIds, int) else []
    if not isinstance(userNames, list):
        userNames = [userNames] if isinstance(userNames, str) else []
    return userIds, userNames


def getMembers(userData: dict, guild: discord.Guild) -> List[discord.Member]:
    userIds, userNames = getUserSearchData(userData)

    members: list = []
    for ids in userIds:
        member: discord.Member | None = guild.get_member(ids)
        if member is not None:
            members.append(member)
    for name in userNames:
        member: discord.Member | None = discord.utils.get(guild.members, name=name)
        if member is not None:
            members.append(member)
    return members


def memberHasRole(member: discord.Member, role: discord.Role) -> bool:
    return member.get_role(role.id) is not None