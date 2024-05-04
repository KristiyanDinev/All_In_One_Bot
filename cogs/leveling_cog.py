
from cogs.ext.utils import *

async def setup(bot: commands.Bot):
    # guilds=[discord.Object(id=....)]
    await bot.add_cog(LevelingCog(bot))




class LevelingCog(commands.Cog, name="Leveling"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(description=configManager.getCommandArgDescription("level", "description"))
    @app_commands.describe(member=configManager.getCommandArgDescription("level", configManager.getMentionMemberKey()))
    async def level(self, interaction: discord.Interaction, member: str = ""):
        if await handleRestricted(self.bot, interaction, "level"):
            return

        if member == "":
            member: discord.Member = interaction.user
        else:
            member: discord.Member = getMember(interaction, get_member_id_from_mention(member))

        if member is None:
            await handleInvalidMember(self.bot, interaction, "level")
            return

        await handleMessage(self.bot, interaction, "level",
                            placeholders={configManager.getLevelPlaceholder(): configManager.getUserLevel(member.id),
                                          configManager.getXPPlaceholder(): configManager.getUserXP(member.id)})

    @app_commands.command(description=configManager.getCommandArgDescription("xp", "description"))
    @app_commands.describe(member=configManager.getCommandArgDescription("xp", configManager.getMentionMemberKey()))
    async def xp(self, interaction: discord.Interaction, member: str = ""):
        if await handleRestricted(self.bot, interaction, "xp"):
            return

        if member == "":
            member: discord.Member = interaction.user
        else:
            member: discord.Member = getMember(interaction, get_member_id_from_mention(member))

        if member is None:
            await handleInvalidMember(self.bot, interaction, "xp")
            return

        await handleMessage(self.bot, interaction, "xp",
                            placeholders={configManager.getLevelPlaceholder(): configManager.getUserLevel(member.id),
                                          configManager.getXPPlaceholder(): configManager.getUserXP(member.id)})


    @app_commands.command(description=configManager.getCommandArgDescription("editxp", "description"))
    @app_commands.describe(member=configManager.getCommandArgDescription("editxp", configManager.getMentionMemberKey()),
                           xp=configManager.getCommandArgDescription("editxp", configManager.getNumberKey()))
    async def editxp(self, interaction: discord.Interaction, xp: str, member: str = ""):
        if await handleRestricted(self.bot, interaction, "editxp"):
            return

        if not xp.isdigit():
            await handleInvalidArg(self.bot, interaction, "editxp")
            return

        if member == "":
            member: discord.Member = interaction.user
        else:
            member: discord.Member = getMember(interaction, get_member_id_from_mention(member))

        if member is None:
            await handleInvalidMember(self.bot, interaction, "editxp")
            return

        setUserXP(member, int(xp))
        await handleMessage(self.bot, interaction, "editxp",
                            placeholders={configManager.getUsernamePlaceholder(): member.name,
                                          configManager.getLevelPlaceholder(): configManager.getUserLevel(member.id),
                                          configManager.getXPPlaceholder(): configManager.getUserXP(member.id)})


    @app_commands.command(description=configManager.getCommandArgDescription("editlevel", "description"))
    @app_commands.describe(member=configManager.getCommandArgDescription("editlevel", configManager.getMentionMemberKey()),
                           level=configManager.getCommandArgDescription("editlevel", configManager.getNumberKey()))
    async def editlevel(self, interaction: discord.Interaction, level: str, member: str = ""):
        if await handleRestricted(interaction, "editlevel"):
            return

        if not level.isdigit():
            await handleInvalidArg(self.bot, interaction, "editlevel")
            return

        if member == "":
            member: discord.Member = interaction.user
        else:
            member: discord.Member = getMember(interaction, get_member_id_from_mention(member))

        if member is None:
            await handleInvalidMember(self.bot, interaction, "editlevel")
            return

        setUserXP(member, configManager.getLevelXP(int(level)))
        await handleMessage(self.bot, interaction, "editlevel",
                            placeholders={configManager.getUsernamePlaceholder(): member.name,
                                          configManager.getLevelPlaceholder(): level,
                                          configManager.getXPPlaceholder(): configManager.getLevelXP(int(level))})

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        return



