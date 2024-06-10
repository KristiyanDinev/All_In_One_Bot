from cogs.ext.imports import *

configManager = ConfigManager("configs/config", "configs/messages",
                              "configs/warnings",
                              "configs/commands")


def getChannelIdFromMention(channelMention: str) -> int:
    try:
        return int(channelMention.replace("<#", "")[:-1]) if "<#" in channelMention else int(channelMention)
    except Exception:
        return 0


def getVoiceChannelGuild(guild: discord.Guild, channelId: int) -> discord.VoiceChannel | None:
    if channelId == 0:
        return None
    channel = guild.get_channel(channelId)
    return channel if isinstance(channel, discord.VoiceChannel) else None


def addWordsToBlacklist(words: list):
    configManager.getBlacklistedWords().extend(words)
    configManager.updateBlacklistWords(configManager.getBlacklistedWords())
    configManager.saveConfigJSON()


def removeWordsFromBlacklist(words: list):
    configManager.updateBlacklistWords([i for i in configManager.getBlacklistedWords() if i not in words])
    configManager.saveConfigJSON()


async def isUserRestricted(bot: commands.Bot, commandName: str, executionPath: str,
                           interaction: discord.Interaction | None = None,
                           ctx: discord.ext.commands.context.Context | None = None) -> tuple:
    if interaction is None and ctx is None:
        return "", []
    res = configManager.getCommandRestrictions(commandName)
    reason: str = ""
    actionList: list = []

    for option, data in res.items():
        if not isinstance(data, dict):
            if option == "actions":
                if not isinstance(data, list):
                    reason += f"Expected list for messages in command restrictions, but got type {type(data)}"
                else:
                    actionList = data
                continue
            else:
                await messages.handleError(bot, commandName, executionPath,
                                           f"Expected map in command restrictions, but got type {type(data)}",
                                           placeholders=dict(),
                                           interaction=interaction, ctx=ctx)
                reason += f"Expected map for {option} in command restrictions, but got type {type(data)}"
                break
        dataReason = data.get("reason", "")
        userRoleId: list = getRoleIdFromRoles(interaction.user.roles if interaction is not None else ctx.author.roles)
        status = data.get("status", [])
        if option == "all":
            if bool(data.get("status", True)):
                return reason, actionList
            else:
                reason += dataReason
        elif (option == "users_id" and isinstance(status, list) and
              (interaction.user.id if interaction is not None else ctx.author.id) not in status):
            reason += dataReason
        elif option == "any_roles_id" and isinstance(status, list) and anyRolesContains(status, userRoleId):
            reason += dataReason
        elif option == "all_roles_id" and isinstance(status, list) and allRolesContains(status, userRoleId):
            reason += dataReason
        elif (option == "channels_id" and isinstance(status, list) and
              (interaction.channel.id if interaction is not None else ctx.channel.id) not in status):
            reason += dataReason

    return reason, actionList


def separateThread(loop, func, *args):
    asyncio.run_coroutine_threadsafe(func(*args), loop)


def getColour(color: str) -> discord.Colour:
    try:
        return discord.Colour.random() if color == "random" or len(color) == 0 else discord.Colour.from_str(color)
    except Exception:
        return discord.Color.red()


def getDiscordPermission(permissions: dict) -> discord.Permissions:
    return discord.Permissions(**permissions)


def getGuildData(guild: discord.Guild) -> dict:
    data = dict()
    data["name"] = guild.name
    data["banner"] = guild.banner
    data["id"] = guild.id
    data["afk_channel_id"] = guild.afk_channel.id if guild.afk_channel is not None else 0
    data["afk_timeout"] = guild.afk_timeout
    data["member_count"] = guild.member_count
    data["bitrate_limit"] = guild.bitrate_limit
    data["created_at"] = guild.created_at
    data["default_notifications"] = str(guild.default_notifications.name)
    data["description"] = guild.description if guild.description is not None else ""
    data["emoji_limit"] = guild.emoji_limit
    data["icon_url"] = guild.icon.__str__() if guild.icon is not None else ""
    data["icon"] = rq.get(guild.icon.__str__()).content if guild.icon is not None else ""
    data["widget_enabled"] = guild.widget_enabled
    data["verification_level"] = str(guild.verification_level.name)
    data["large"] = guild.large
    data["max_members"] = guild.max_members if guild.max_members is not None else 0
    data["max_presences"] = guild.max_presences if guild.max_presences is not None else 0
    data["max_stage_video_users"] = guild.max_stage_video_users if guild.max_stage_video_users is not None else 0
    data["max_video_channel_users"] = guild.max_video_channel_users if guild.max_video_channel_users is not None else 0
    data["mfa_level"] = str(guild.mfa_level.name)
    data["nsfw_level"] = str(guild.nsfw_level.name)
    data["owner_id"] = guild.owner.id
    data["owner_name"] = guild.owner.name
    data["preferred_locale"] = str(guild.preferred_locale.name)
    data["premium_progress_bar_enabled"] = guild.premium_progress_bar_enabled
    data["content_filter"] = str(guild.explicit_content_filter.name)
    data["premium_subscription_count"] = guild.premium_subscription_count
    data["premium_tier"] = guild.premium_tier
    data["public_updates_channel_name"] = guild.public_updates_channel.name \
        if guild.public_updates_channel is not None else ""
    data["public_updates_channel_id"] = guild.public_updates_channel.id \
        if guild.public_updates_channel is not None else 0
    data["rules_channel_name"] = guild.rules_channel.name if guild.rules_channel is not None else ""
    data["rules_channel_id"] = guild.rules_channel.id if guild.rules_channel is not None else 0
    data["shard_id"] = guild.shard_id
    data["vanity_url"] = guild.vanity_url if guild.vanity_url is not None else ""
    data["vanity_url_code"] = guild.vanity_url_code if guild.vanity_url_code is not None else ""
    data["widget_channel_name"] = guild.widget_channel.name if guild.widget_channel is not None else ""
    data["widget_channel_id"] = guild.widget_channel.id if guild.widget_channel is not None else 0
    data["filesize_limit"] = guild.filesize_limit
    data["safety_alerts_channel_name"] = guild.safety_alerts_channel.name \
        if guild.safety_alerts_channel is not None else ""
    data["safety_alerts_channel_id"] = guild.safety_alerts_channel.id \
        if guild.safety_alerts_channel is not None else ""
    data["sticker_limit"] = guild.sticker_limit
    data["unavailable"] = guild.unavailable
    data["system_channel_name"] = guild.system_channel.name if guild.system_channel is not None else ""
    data["system_channel_id"] = guild.system_channel.id if guild.system_channel is not None else 0
    data["chunked"] = guild.chunked
    data["splash_url"] = guild.splash.__str__() if guild.splash is not None else ""
    data["splash"] = rq.get(guild.splash.__str__()).content if guild.splash is not None else ""
    data["discovery_splash_url"] = guild.discovery_splash.__str__() if guild.splash is not None else ""
    data["discovery_splash"] = rq.get(guild.discovery_splash.__str__()).content if guild.splash is not None else ""
    data["system_channel_flags"] = {flag: getattr(guild.system_channel_flags, flag)
                                    for flag, value in discord.SystemChannelFlags.VALID_FLAGS.items()}
    data["guild_features"] = guild.features
    return data


async def editGuild(guildData: dict, guild: discord.Guild, reason: str = ""):
    for key in guildData.keys():
        if key == "owner_id":
            ownerId: str = str(guildData.get("owner_id", ""))
            if ownerId.isdigit():
                ownerId = int(ownerId)
            else:
                ownerId = 0
            await guild.edit(reason=reason, owner=getMemberGuild(guild, ownerId))
        elif key == "afk_channel_id":
            afk_channel: str = str(guildData.get("afk_channel_id", ""))
            afk_channel_obj = getVoiceChannelGuild(guild, int(afk_channel) if afk_channel.isdigit() else 0)
            if afk_channel_obj != guild.afk_channel:
                await guild.edit(reason=reason, afk_channel=afk_channel_obj)
        elif key == "system_channel_id":
            system_channel: str = str(guildData.get("system_channel_id", ""))
            system_channel_obj = getVoiceChannelGuild(guild,
                                                      int(system_channel) if system_channel.isdigit() else 0)
            if system_channel_obj != guild.system_channel:
                await guild.edit(reason=reason, afk_channel=system_channel_obj)
        elif key == "afk_timeout":
            afk_timeout: str = str(guildData.get("afk_timeout", ""))
            if afk_timeout.isdigit() and int(afk_timeout) != guild.afk_timeout:
                await guild.edit(reason=reason, afk_timeout=int(afk_timeout))
        elif key == "rules_channel_id":
            rules_channel: str = str(guildData.get("rules_channel_id", ""))
            rules_channel_obj = getTextChannel(guild, int(rules_channel) if rules_channel.isdigit() else 0)
            if rules_channel_obj != guild.rules_channel:
                await guild.edit(reason=reason, rules_channel=rules_channel_obj)
        elif key == "public_updates_channel_id":
            public_updates_channel: str = str(guildData.get("public_updates_channel_id", ""))
            public_updates_channel_obj = getTextChannel(guild,
                                                        int(public_updates_channel)
                                                        if public_updates_channel.isdigit() else 0)
            if public_updates_channel_obj != guild.rules_channel:
                await guild.edit(reason=reason, public_updates_channel=public_updates_channel_obj)
        elif key == "widget_channel_id":
            widget_channel: str = str(guildData.get("widget_channel_id", ""))
            widget_channel_obj = getTextChannel(guild, int(widget_channel) if widget_channel.isdigit() else 0)
            if widget_channel_obj != guild.widget_channel:
                await guild.edit(reason=reason, widget_channel=widget_channel_obj)
        elif key == "safety_alerts_channel_id":
            safety_alerts_channel: str = str(guildData.get("safety_alerts_channel_id", ""))
            if safety_alerts_channel.isdigit() and int(
                    safety_alerts_channel) != guild.safety_alerts_channel.id:
                await guild.edit(reason=reason,
                                 safety_alerts_channel=getTextChannel(guild, int(safety_alerts_channel)))
        elif key == "description":
            description = guildData.get("description")
            if guild.description != description:
                await guild.edit(reason=reason, description=description)
        elif key == "icon":
            icon = guildData.get("icon")
            if icon is bytes and guild.icon != icon:
                await guild.edit(reason=reason, icon=icon)
        elif key == "name":
            name: str = str(guildData.get("name", ""))
            if name is not None and guild.name != name and len(name.replace(" ", "")) > 0:
                await guild.edit(reason=reason, name=name)
        elif key == "banner":
            banner = guildData.get("banner")
            if guild.banner != banner:
                await guild.edit(reason=reason, banner=banner)
        elif key == "splash":
            splash = guildData.get("splash")
            if splash is bytes and rq.get(guild.splash.url).content != splash:
                await guild.edit(reason=reason, splash=splash)
        elif key == "discovery_splash":
            discovery_splash = guildData.get("discovery_splash")
            if discovery_splash is bytes and rq.get(guild.discovery_splash.url).content != discovery_splash:
                await guild.edit(reason=reason, discovery_splash=discovery_splash)
        elif key == "default_notifications":
            default_notifications: discord.NotificationLevel | None = getattr(discord.NotificationLevel,
                                                                              str(guildData.get(
                                                                                  "default_notifications")).lower(),
                                                                              None)
            if default_notifications is not None and guild.default_notifications != default_notifications:
                await guild.edit(reason=reason, default_notifications=default_notifications)
        elif key == "verification_level":
            verification_level: discord.VerificationLevel | None = getattr(discord.VerificationLevel,
                                                                           str(guildData.get(
                                                                               "verification_level")).lower(),
                                                                           None)
            if verification_level is not None and guild.verification_level != verification_level:
                await guild.edit(reason=reason, verification_level=verification_level)
        elif key == "content_filter":
            explicit_content_filter: discord.ContentFilter | None = getattr(discord.ContentFilter,
                                                                            str(guildData.get(
                                                                                "content_filter")).lower(),
                                                                            None)
            if explicit_content_filter is not None and guild.explicit_content_filter != explicit_content_filter:
                await guild.edit(reason=reason, explicit_content_filter=explicit_content_filter)
        elif key == "preferred_locale":
            preferred_locale: discord.Locale | None = getattr(discord.Locale,
                                                              str(guildData.get(
                                                                  "preferred_locale")).lower(),
                                                              None)
            if preferred_locale is not None and preferred_locale != guild.preferred_locale:
                await guild.edit(reason=reason, preferred_locale=preferred_locale)
        elif key == "mfa_level":
            mfa_level: discord.MFALevel | None = getattr(discord.MFALevel,
                                                         str(guildData.get("mfa_level")).lower(),
                                                         None)
            if mfa_level is not None and mfa_level != guild.mfa_level:
                await guild.edit(reason=reason, mfa_level=mfa_level)
        elif key == "vanity_code":
            vanity_code: str | None = guildData.get("vanity_code", None)
            if vanity_code is not None:
                await guild.edit(reason=reason, vanity_code=vanity_code)
        elif key == "discoverable":
            await guild.edit(reason=reason, discoverable=bool(guildData.get("discoverable")))
        elif key == "invites_disabled":
            await guild.edit(reason=reason, invites_disabled=bool(guildData.get("invites_disabled")))
        elif key == "raid_alerts_disabled":
            await guild.edit(reason=reason,
                             raid_alerts_disabled=bool(guildData.get("raid_alerts_disabled")))
        elif key == "community":
            await guild.edit(reason=reason, community=bool(guildData.get("community")))


def getTextChannel(guild: discord.Guild, channelId: int) -> discord.TextChannel | None:
    if channelId == 0:
        return None
    channel = guild.get_channel(channelId)
    return channel if type(channel) == discord.TextChannel else None


def getPermissionsMapping(permissions: dict, guild: discord.Guild) -> Mapping[
    Union[Role, discord.Member], discord.PermissionOverwrite]:
    overwrites = {}
    users: list = permissions.get("users")
    roles: list = permissions.get("roles")
    if not isinstance(users, list):
        users = []
    if not isinstance(roles, list):
        roles = []
    for role in roles:
        if not isinstance(role, dict):
            continue
        for r in getRoles(role, guild):
            perms = role.get("permissions")
            if not isinstance(perms, dict):
                continue
            overwrites[r] = discord.PermissionOverwrite(**perms)
    for user in users:
        if not isinstance(user, dict):
            continue
        for u in getMembers(user, guild):
            perms = user.get("permissions")
            if not isinstance(perms, dict):
                continue
            overwrites[u] = discord.PermissionOverwrite(**perms)

    return overwrites


def getPermissionsDataFromMapping(mapping: Mapping[Union[Role, discord.Member], discord.PermissionOverwrite]) -> dict:
    data: dict = dict()
    data["roles"] = []
    data["users"] = []
    for obj, permoverride in mapping.items():
        if isinstance(obj, discord.Role):
            roleData: dict = dict()
            roleData["role_name"] = obj.name
            roleData["role_id"] = obj.id
            roleData["permissions"] = dict()
            for name in permoverride.VALID_NAMES:
                res = getattr(permoverride, name, None)
                if res is None:
                    continue
                roleData["permissions"][name] = res
            data["roles"].append(roleData)
        elif isinstance(obj, discord.User) or isinstance(obj, discord.Member):
            userData: dict = dict()
            userData["user_name"] = obj.name
            userData["user_id"] = obj.id
            userData["permissions"] = dict()
            for name in permoverride.VALID_NAMES:
                res = getattr(permoverride, name, None)
                if res is None:
                    continue
                userData["permissions"][name] = res
            data["users"].append(userData)
    return data
