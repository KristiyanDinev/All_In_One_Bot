from __future__ import annotations

import discord.errors
from cogs.ext.utils import *


async def setup(bot: commands.Bot):
    # guilds=[discord.Object(id=....)]
    await bot.add_cog(UtilsCog(bot))


class UtilsCog(commands.Cog, name="Utils"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(description=configManager.getCommandArgDescription("disablecog", "description"))
    @app_commands.describe(cog=configManager.getCommandArgDescription("disablecog", configManager.getEnterMessageKey()))
    async def disablecog(self, interaction: discord.Interaction, cog: str):
        if await handleRestricted(self.bot, interaction, "disablecog"):
            return

        if len(cog.replace(" ", "")) == 0:
            await handleInvalidArg(self.bot, interaction, "disablecog")
            return

        given_cog_file_name: str | None = CogsData.get(cog)
        if given_cog_file_name is None:
            await handleInvalidArg(self.bot, interaction, "disablecog")
            return

        try:
            await self.bot.unload_extension(f"cogs.{given_cog_file_name}")
            await handleMessage(self.bot, interaction, "disablecog",
                                placeholders={configManager.getUsernamePlaceholder(): cog})
        except Exception as e:
            await handleErrors(self.bot, interaction, "disablecog", e)


    @app_commands.command(description=configManager.getCommandArgDescription("enablecog", "description"))
    @app_commands.describe(cog=configManager.getCommandArgDescription("enablecog", configManager.getEnterMessageKey()))
    async def enablecog(self, interaction: discord.Interaction, cog: str):
        if await handleRestricted(self.bot, interaction, "enablecog"):
            return

        if len(cog.replace(" ", "")) == 0:
            await handleInvalidArg(self.bot, interaction, "enablecog")
            return

        given_cog_file_name: str | None = CogsData.get(cog)
        if given_cog_file_name is None:
            await handleInvalidArg(self.bot, interaction, "enablecog")
            return

        try:
            await self.bot.load_extension(f"cogs.{given_cog_file_name}")
            await handleMessage(self.bot, interaction, "enablecog",
                                placeholders={configManager.getUsernamePlaceholder(): cog})
        except Exception as e:
            await handleErrors(self.bot, interaction, "enablecog", e)

    @app_commands.command(description=configManager.getCommandArgDescription("listcog", "description"))
    async def listcog(self, interaction: discord.Interaction):
        if await handleRestricted(self.bot, interaction, "listcog"):
            return

        for name, file_name in CogsData.items():
            try:
                await self.bot.load_extension(f"cogs.{file_name}")

            except commands.ExtensionAlreadyLoaded:
                #await ctx.send("Cog is loaded")
                await handleMessage(self.bot, interaction, "listcog",
                                    placeholders={configManager.getUsernamePlaceholder(): name,
                                                  configManager.getMessagePlaceholder(): configManager.getCogActiveStatus()})

            except commands.ExtensionNotFound:
                #await ctx.send("Cog not found")
                await handleMessage(self.bot, interaction, "listcog",
                                    placeholders={configManager.getUsernamePlaceholder(): name,
                                                  configManager.getMessagePlaceholder(): configManager.getCogNotFoundStatus()})
            else:
                #await ctx.send("Cog is unloaded")
                await self.bot.unload_extension(f"cogs.{file_name}")
                await handleMessage(self.bot, interaction, "listcog",
                                    placeholders={configManager.getUsernamePlaceholder(): name,
                                                  configManager.getMessagePlaceholder(): configManager.getCogDeactiveStatus()})


