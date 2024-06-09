from __future__ import annotations

import discord.errors
from discord import app_commands
from cogs.ext.utils.utils import *
import cogs.ext.messages as messages

async def setup(bot: commands.Bot):
    # guilds=[discord.Object(id=....)]
    await bot.add_cog(UtilsCog(bot))


class UtilsCog(commands.Cog, name="Utils"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(description=configManager.getCommandArgDescription("disablecog", "description"))
    @app_commands.describe(cog=configManager.getCommandArgDescription("disablecog", configManager.getEnterMessageKey()))
    async def disablecog(self, interaction: discord.Interaction, cog: str):
        if await messages.handleRestricted(self.bot, interaction, "disablecog"):
            return

        if len(cog.replace(" ", "")) == 0:
            await messages.handleInvalidArg(self.bot, interaction, "disablecog")
            return

        given_cog_file_name: str | None = configManager.getCogData().get(cog, None)
        if given_cog_file_name is None:
            await messages.handleInvalidArg(self.bot, interaction, "disablecog")
            return

        try:
            await self.bot.unload_extension(f"cogs.{given_cog_file_name}")
            await messages.handleMessage(self.bot, interaction, "disablecog",
                                         placeholders={configManager.getUsernamePlaceholder(): cog})
        except Exception as e:
            await messages.handleErrors(self.bot, interaction, "disablecog", e)


    @app_commands.command(description=configManager.getCommandArgDescription("enablecog", "description"))
    @app_commands.describe(cog=configManager.getCommandArgDescription("enablecog", configManager.getEnterMessageKey()))
    async def enablecog(self, interaction: discord.Interaction, cog: str):
        if await messages.handleRestricted(self.bot, interaction, "enablecog"):
            return

        if len(cog.replace(" ", "")) == 0:
            await messages.handleInvalidArg(self.bot, interaction, "enablecog")
            return

        given_cog_file_name: str | None = configManager.getCogData.get(cog, None)
        if given_cog_file_name is None:
            await messages.handleInvalidArg(self.bot, interaction, "enablecog")
            return

        try:
            await self.bot.load_extension(f"cogs.{given_cog_file_name}")
            await messages.handleMessage(self.bot, interaction, "enablecog",
                                         placeholders={configManager.getUsernamePlaceholder(): cog})
        except Exception as e:
            await messages.handleErrors(self.bot, interaction, "enablecog", e)

    @app_commands.command(description=configManager.getCommandArgDescription("listcog", "description"))
    async def listcog(self, interaction: discord.Interaction):
        if await messages.handleRestricted(self.bot, interaction, "listcog"):
            return

        for name, file_name in configManager.getCogData().items():
            try:
                await self.bot.load_extension(f"cogs.{file_name}")

            except commands.ExtensionAlreadyLoaded:
                #await ctx.send("Cog is loaded")
                await messages.handleMessage(self.bot, interaction, "listcog",
                                             placeholders={configManager.getUsernamePlaceholder(): name,
                                                  configManager.getMessagePlaceholder(): configManager.getCogActiveStatus()})

            except commands.ExtensionNotFound:
                #await ctx.send("Cog not found")
                await messages.handleMessage(self.bot, interaction, "listcog",
                                             placeholders={configManager.getUsernamePlaceholder(): name,
                                                  configManager.getMessagePlaceholder(): configManager.getCogNotFoundStatus()})
            else:
                #await ctx.send("Cog is unloaded")
                await self.bot.unload_extension(f"cogs.{file_name}")
                await messages.handleMessage(self.bot, interaction, "listcog",
                                             placeholders={configManager.getUsernamePlaceholder(): name,
                                                  configManager.getMessagePlaceholder(): configManager.getCogDeactiveStatus()})

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        return


