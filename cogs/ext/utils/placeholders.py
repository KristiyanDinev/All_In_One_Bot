import discord

from cogs.ext.utils import utils


def usePlaceholders(msg: str, placeholders: dict) -> str:
    for placeholder, v in placeholders.items():
        if utils.configManager.isActivePlaceholder(placeholder):
            msg = msg.replace(str(placeholder), str(v))
    return msg


def addDefaultPlaceholder(placeholders: dict, interaction: discord.Interaction = None,
                          ctx: discord.ext.commands.context.Context | None = None):
    actionPath = utils.configManager.getActionPathPlaceholder()
    if actionPath not in placeholders.keys():
        placeholders[actionPath] = ""
    if interaction is not None:
        if utils.configManager.getXPPlaceholder() not in placeholders.keys():
            placeholders[utils.configManager.getXPPlaceholder()] = str(
                utils.configManager.getUserXP(interaction.user.id))

        if utils.configManager.getLevelPlaceholder() not in placeholders.keys():
            placeholders[utils.configManager.getLevelPlaceholder()] = str(
                utils.configManager.getUserLevel(interaction.user.id))

        if utils.configManager.getUsernamePlaceholder() not in placeholders.keys():
            placeholders[utils.configManager.getUsernamePlaceholder()] = interaction.user.name

        if utils.configManager.getIDPlaceholder() not in placeholders.keys():
            placeholders[utils.configManager.getIDPlaceholder()] = str(interaction.user.id)

    elif ctx is not None:
        if utils.configManager.getXPPlaceholder() not in placeholders.keys():
            placeholders[utils.configManager.getXPPlaceholder()] = str(utils.configManager.getUserXP(ctx.author.id))

        if utils.configManager.getLevelPlaceholder() not in placeholders.keys():
            placeholders[utils.configManager.getLevelPlaceholder()] = str(
                utils.configManager.getUserLevel(ctx.author.id))

        if utils.configManager.getUsernamePlaceholder() not in placeholders.keys():
            placeholders[utils.configManager.getUsernamePlaceholder()] = ctx.author.name

        if utils.configManager.getIDPlaceholder() not in placeholders.keys():
            placeholders[utils.configManager.getIDPlaceholder()] = str(ctx.author.id)

    return placeholders



