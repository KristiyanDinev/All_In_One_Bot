from cogs.ext.imports import *


def getChannels(channelData: dict, guild: discord.Guild) -> list:
    channelIds = channelData.get("channel_id")
    channelNames = channelData.get("channel_name")
    if isinstance(channelIds, int):
        channelIds = [channelIds]
    elif not isinstance(channelIds, list):
        channelIds = []

    if isinstance(channelNames, str):
        channelNames = [channelNames]
    elif not isinstance(channelNames, list):
        channelNames = []

    channels: list = []
    for ids in channelIds:
        for cha in guild.channels:
            if cha.id == ids:
                channels.append(cha)
    for name in channelNames:
        for cha in guild.channels:
            if cha.name == name:
                channels.append(cha)

    category_name = channelData.get("category_name")
    if isinstance(category_name, str):
        category_name = [category_name]
    if not isinstance(category_name, list):
        category_name = []

    category_id = channelData.get("category_id")
    if isinstance(category_id, int):
        category_id = [category_id]
    if not isinstance(category_id, list):
        category_id = []

    for i in range(len(channels)):
        channel = channels[i]
        if not (channel.category is not None and (
                channel.category.id in category_id or channel.category.name in category_name)):
            channels.pop(i)
    return channels


async def createChannel(channelData: dict, guild: discord.Guild) -> List[discord.abc.GuildChannel]:
    channel_type: str = str(channelData.get("type")).lower()
    permissions = channelData.get("permissions")
    if not isinstance(permissions, dict):
        permissions = dict()

    position: int = channelData.get("position")
    if not isinstance(position, int):
        position = 1

    bitrate: int | None = channelData.get("bitrate")
    if not isinstance(bitrate, int):
        bitrate = 64

    user_limit: int | None = channelData.get("user_limit")
    if not isinstance(user_limit, int):
        user_limit = None

    video_quality_mode: discord.VideoQualityMode | None = getattr(discord.VideoQualityMode,
                                                                  str(channelData.get("video_quality_mode", "")),
                                                                  None)

    overwrite = getPermissionsMapping(permissions, guild)
    createdChannels: list = []
    categories = [None]
    if "category_name" in channelData.keys() or "category_id" in channelData.keys():
        categories = getCategories(channelData, guild)
    for category in categories:
        if channel_type == "voice":
            channel = await guild.create_voice_channel(name=str(channelData.get("name", "ChannelName")),
                                                       reason=str(channelData.get("reason")), category=category,
                                                       position=position,
                                                       rtc_region=channelData.get("rtc_region", None),
                                                       overwrites=overwrite)
            if bitrate is not None:
                await channel.edit(bitrate=bitrate)
            if user_limit is not None:
                await channel.edit(user_limit=user_limit)
            if video_quality_mode is not None:
                await channel.edit(video_quality_mode=video_quality_mode)
            createdChannels.append(channel)
        elif channel_type == "stage":
            channel = await guild.create_stage_channel(name=str(channelData.get("name", "ChannelName")),
                                                       reason=str(channelData.get("reason")), category=category,
                                                       position=position,
                                                       rtc_region=channelData.get("rtc_region", None),
                                                       overwrites=overwrite, bitrate=bitrate)
            if user_limit is not None:
                await channel.edit(user_limit=user_limit)
            if video_quality_mode is not None:
                await channel.edit(video_quality_mode=video_quality_mode)
            createdChannels.append(channel)
        elif channel_type == "form":
            channel = await guild.create_forum(name=str(channelData.get("name", "ChannelName")),
                                               reason=str(channelData.get("reason")), category=category,
                                               position=position, nsfw=bool(channelData.get("nsfw", False)),
                                               overwrites=overwrite)
            if "topic" in channelData.keys():
                await channel.edit(topic=str(channelData.get("topic")))

            slowmode_delay = channelData.get("slowmode_delay")
            if isinstance(slowmode_delay, int):
                await channel.edit(slowmode_delay=slowmode_delay)

            default_auto_archive_duration = channelData.get("default_auto_archive_duration")
            if isinstance(default_auto_archive_duration, int):
                await channel.edit(default_auto_archive_duration=default_auto_archive_duration)

            default_thread_slowmode_delay = channelData.get("default_thread_slowmode_delay")
            if isinstance(default_thread_slowmode_delay, int):
                await channel.edit(default_thread_slowmode_delay=default_thread_slowmode_delay)

            default_sort_order = getattr(discord.ForumOrderType, str(channelData.get("default_sort_order", "")),
                                         None)
            if default_sort_order is not None:
                await channel.edit(default_sort_order=default_sort_order)

            default_reaction_emoji = channelData.get("default_reaction_emoji", None)
            if default_reaction_emoji is not None:
                await channel.edit(default_reaction_emoji=str(default_reaction_emoji))

            default_layout = getattr(discord.ForumLayoutType, str(channelData.get("default_layout", "")),
                                     None)
            if default_layout is not None:
                await channel.edit(default_layout=default_layout)

            available_tags = channelData.get("available_tags")
            if isinstance(available_tags, list):
                await channel.edit(available_tags=available_tags)

            createdChannels.append(channel)
        else:
            channel = await guild.create_text_channel(name=str(channelData.get("name", "ChannelName")),
                                                      reason=str(channelData.get("reason")), category=category,
                                                      position=position,
                                                      overwrites=overwrite, news=bool(channelData.get("news", False)),
                                                      nsfw=bool(channelData.get("nsfw", False)))
            if "topic" in channelData.keys():
                await channel.edit(topic=str(channelData.get("topic")))

            slowmode_delay = channelData.get("slowmode_delay")
            if isinstance(slowmode_delay, int):
                await channel.edit(slowmode_delay=slowmode_delay)

            default_auto_archive_duration = channelData.get("default_auto_archive_duration")
            if isinstance(default_auto_archive_duration, int):
                await channel.edit(default_auto_archive_duration=default_auto_archive_duration)

            default_thread_slowmode_delay = channelData.get("default_thread_slowmode_delay")
            if isinstance(default_thread_slowmode_delay, int):
                await channel.edit(default_thread_slowmode_delay=default_thread_slowmode_delay)

            createdChannels.append(channel)
    return createdChannels


async def deleteChannel(channel: discord.abc.GuildChannel, reason: str = ""):
    await channel.delete(reason=reason)


def getChannelData(channel: discord.abc.GuildChannel) -> dict:
    data: dict = dict()
    data["name"] = channel.name
    data["permissions"] = getPermissionsDataFromMapping(channel.overwrites)
    data["position"] = channel.position
    if channel.category is not None:
        data["category_id"] = channel.category.id
        data["category_name"] = channel.category.name
    if isinstance(channel, discord.TextChannel):
        data["topic"] = channel.topic
        data["slowmode_delay"] = channel.slowmode_delay
        data["default_thread_slowmode_delay"] = channel.default_thread_slowmode_delay
        data["default_auto_archive_duration"] = channel.default_auto_archive_duration
    elif isinstance(channel, discord.VoiceChannel):
        data["bitrate"] = channel.bitrate
        data["user_limit"] = channel.user_limit
        data["video_quality_mode"] = channel.video_quality_mode
        data["rtc_region"] = channel.rtc_region
    elif isinstance(channel, discord.StageChannel):
        data["user_limit"] = channel.user_limit
        data["video_quality_mode"] = channel.video_quality_mode
        data["rtc_region"] = channel.rtc_region
    elif isinstance(channel, discord.ForumChannel):
        data["nsfw"] = channel.nsfw
        data["topic"] = channel.topic
        data["slowmode_delay"] = channel.slowmode_delay
        data["default_auto_archive_duration"] = channel.default_auto_archive_duration
        data["default_thread_slowmode_delay"] = channel.default_thread_slowmode_delay
        data["default_sort_order"] = channel.default_sort_order
        data["default_reaction_emoji"] = channel.default_reaction_emoji
        data["default_layout"] = channel.default_layout
        data["available_tags"] = channel.available_tags
    return data


async def editChannel(channelData: dict,
                      channel: discord.abc.GuildChannel):
    channelDataCopy = channelData.copy()
    channelDataCopy["category_name"] = channelDataCopy.pop("new_category_name")
    channelDataCopy["category_id"] = channelDataCopy.pop("new_category_id")
    permissions = channelDataCopy.get("permissions")
    if not isinstance(permissions, dict):
        permissions = dict()
    overwrites = getPermissionsMapping(permissions, channel.guild)
    video_quality_mode: discord.VideoQualityMode | None = getattr(discord.VideoQualityMode,
                                                                  str(channelDataCopy.get("video_quality_mode",
                                                                                          "")),
                                                                  None)
    for new_category in getCategories(channelDataCopy, channel.guild):
        position: int = channelDataCopy.get("position")
        if isinstance(position, int):
            await channel.edit(position=position)

        slowmode_delay: int = channelDataCopy.get("slowmode_delay")
        if isinstance(slowmode_delay, int):
            await channel.edit(slowmode_delay=slowmode_delay)

        new_name = str(channelDataCopy.get("new_name", channel.name))
        reason = str(channelDataCopy.get("reason", ""))
        nsfw = bool(channelDataCopy.get("nsfw", False))
        sync_permissions = bool(channelDataCopy.get("sync_permissions", False))
        if isinstance(channel, discord.TextChannel):
            await channel.edit(name=new_name, reason=reason, nsfw=nsfw, sync_permissions=sync_permissions,
                               category=new_category, overwrites=overwrites)
            if "topic" in channelDataCopy.keys():
                await channel.edit(topic=str(channelDataCopy.get("topic")))

            default_auto_archive_duration: int = channelDataCopy.get("default_auto_archive_duration")
            if isinstance(default_auto_archive_duration, int):
                await channel.edit(default_auto_archive_duration=default_auto_archive_duration)

            default_thread_slowmode_delay: int = channelDataCopy.get("default_thread_slowmode_delay")
            if isinstance(default_thread_slowmode_delay, int):
                await channel.edit(default_thread_slowmode_delay=default_thread_slowmode_delay)
        elif isinstance(channel, discord.VoiceChannel):
            await channel.edit(name=new_name, reason=reason, nsfw=nsfw, sync_permissions=sync_permissions,
                               category=new_category, overwrites=overwrites,
                               rtc_region=None if not isinstance(channelDataCopy.get("rtc_region", None), str)
                               else channelDataCopy.get("rtc_region"))

            user_limit: int = channelDataCopy.get("user_limit")
            if isinstance(user_limit, int):
                await channel.edit(user_limit=user_limit)
            bitrate: int = channelDataCopy.get("bitrate")
            if isinstance(bitrate, int):
                await channel.edit(bitrate=bitrate)

            if video_quality_mode is not None:
                await channel.edit(video_quality_mode=video_quality_mode)
        elif isinstance(channel, discord.StageChannel):
            await channel.edit(name=new_name, reason=reason, nsfw=nsfw, sync_permissions=sync_permissions,
                               category=new_category, overwrites=overwrites,
                               rtc_region=None if not isinstance(channelDataCopy.get("rtc_region", None), str)
                               else channelDataCopy.get("rtc_region"))

            user_limit: int = channelDataCopy.get("user_limit")
            if isinstance(user_limit, int):
                await channel.edit(user_limit=user_limit)

            if video_quality_mode is not None:
                await channel.edit(video_quality_mode=video_quality_mode)
        elif isinstance(channel, discord.ForumChannel):
            await channel.edit(name=new_name, reason=reason, nsfw=nsfw, sync_permissions=sync_permissions,
                               category=new_category, overwrites=overwrites)

            if "topic" in channelDataCopy.keys():
                await channel.edit(topic=str(channelDataCopy.get("topic")))

            default_auto_archive_duration: int = channelDataCopy.get("default_auto_archive_duration")
            if isinstance(default_auto_archive_duration, int):
                await channel.edit(default_auto_archive_duration=default_auto_archive_duration)

            available_tags = channelData.get("available_tags")
            if isinstance(available_tags, list):
                await channel.edit(available_tags=available_tags)


