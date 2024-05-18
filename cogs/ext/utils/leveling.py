from __future__ import annotations

import discord
import cogs.ext.utils.utils as utils


def getUserLevel(user: discord.Member, isMax: bool) -> int:
    if isMax:
        res: int | None = utils.configManager.getLevelExceptionalUserMax(user.id)
    else:
        res: int | None = utils.configManager.getLevelExceptionalUserMin(user.id)

    if res is not None:
        return int(res)

    userRoleIds: list = utils.getRoleIdFromRoles(user.roles)
    if len(userRoleIds) == 0:
        return utils.configManager.getLevelGlobalMax() if isMax else utils.configManager.getLevelGlobalMin()

    biggestLimit: int | None = None
    for roleId in userRoleIds:
        if isMax:
            roleMax: int | None = utils.configManager.getLevelExceptionalRoleMax(roleId)
            if (roleMax is not None) and ((biggestLimit is None) or (roleMax > biggestLimit)):
                biggestLimit = roleMax
        else:
            roleMax: int | None = utils.configManager.getLevelExceptionalRoleMin(roleId)
            if (roleMax is not None) and ((biggestLimit is None) or (roleMax < biggestLimit)):
                biggestLimit = roleMax

    return biggestLimit if biggestLimit is not None else (
        utils.configManager.getLevelGlobalMax() if isMax else utils.configManager.getLevelGlobalMin())


def getLevelByXP(xp: int):
    level = 0
    while True:
        if xp == utils.configManager.getLevelXP(level) or xp < utils.configManager.getLevelXP(level + 1):
            break
        level += 1
    return level


def setUserXP(user: discord.Member, xp: int):
    maxLevel = getUserLevel(user, True)
    minLevel = getUserLevel(user, False)
    currentLevel = utils.configManager.getUserLevel(user.id)

    if minLevel > currentLevel or currentLevel > maxLevel or maxLevel == minLevel:
        utils.configManager.setUserLevel(user.id, minLevel)
        utils.configManager.setUserXP(user.id, utils.configManager.getLevelXP(minLevel))
        utils.configManager.saveLevelJSON()
        return

    utils.configManager.setUserXP(user.id, xp)
    utils.configManager.setUserLevel(user.id, getLevelByXP(xp))

    utils.configManager.saveLevelJSON()
