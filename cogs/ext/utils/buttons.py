from __future__ import annotations

import discord
from discord.ext import commands
import cogs.ext.utils.utils as utils
import cogs.ext.utils.actions as actions
import cogs.ext.utils.placeholders as placeholders_utils


class ViewButton(discord.ui.Button):
    def __init__(self, data: dict, bot: commands.Bot, **kwargs):
        super().__init__(**kwargs)
        self.actions: list = list(data['actions']).copy()
        self.bot = bot
        # 'idk' -> [1, 2, 3]

        self.actionData: dict = dict()
        # 'idk' -> {'messages' : [....]}

        for action in self.actions:
            self.actionData[action] = utils.configManager.getActionData(action).copy()

    async def callback(self, interaction: discord.Interaction):
        await actions.handleAllActions(self.actionData, interaction)


class TempView(discord.ui.View):
    is_active_placeholder = False
    allButtonLabels = []
    view = ""
    timeout = None
    bot = None

    def __init__(self):
        super().__init__(timeout=self.timeout)
        if len(self.view) > 0:
            self.allButtonLabels = utils.configManager.getButtonsByView(self.view)
            for label in self.allButtonLabels:
                comb = self.view.replace(" ", "") + " " + str(label).replace(" ", "")

                self.add_item(ViewButton(label=label,
                                         style=getattr(discord.ButtonStyle, utils.configManager.getButtonStyle(comb)),
                                         custom_id=utils.configManager.getButtonCustomID(comb),
                                         bot=self.bot,
                                         data={"actions": utils.configManager.getActions(comb)}))

    if timeout is None:
        async def on_timeout(self):
            for child in self.children:
                child.disabled = False


def buildButtonData(bot: commands.Bot, msg: str, placeholders: dict) -> discord.ui.View | None:
    if not utils.configManager.hasButton(msg) or bot is None:
        return None

    eph = utils.configManager.getEphPlaceholder()
    TempView.view = placeholders_utils.usePlaceholders(msg, placeholders)
    TempView.bot = bot
    TempView.timeout = utils.configManager.getButtonTimeout(msg)
    TempView.is_active_placeholder = utils.configManager.isActivePlaceholder(eph) and eph in msg
    return TempView
