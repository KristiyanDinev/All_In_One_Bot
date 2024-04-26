from __future__ import annotations

from cogs.ext.utils import *

async def setup(bot: commands.Bot):
    pass

class ConfigManager:
    def __init__(self, file_path, messages_path, warnings_path, commands_folder):
        self.config_path = file_path
        self.message_path = messages_path
        self.warning_path = warnings_path
        self.command_folder = commands_folder
        self.warning_data = self._readJSON(warnings_path)
        self.data = self._readJSON(file_path)
        self.messages = self._readJSON(messages_path)

    def saveCommandJSON(self, command: str, command_data: dict) -> None:
        self._saveJSON(self.command_folder+"/"+command+".json", command_data)

    def saveConfigJSON(self) -> None:
        self._saveJSON(self.config_path, self.data)

    def saveWarningsJSON(self) -> None:
        self._saveJSON(self.warning_path, self.warning_data)

    def saveMessagesJSON(self) -> None:
        self._saveJSON(self.message_path, self.messages)

    def _saveJSON(self, output_file_name, data) -> None:
        open(output_file_name + ".json", "a")
        with open(output_file_name + ".json", "w") as jsonfile:
            json.dump(data, jsonfile, indent=4)

    def _readJSON(self, file_name) -> dict:
        if not os.path.exists(file_name + ".json"):
            return {}

        with open(file_name + ".json", "r") as jsonfile:
            return json.load(jsonfile)

    def reloadConfig(self):
        self.warning_data = self._readJSON(self.warning_path)
        self.data = self._readJSON(self.config_path)
        self.messages = self._readJSON(self.message_path)

    def getBotToken(self):
        return self.data.get("discord_bot_token")

    def getBotPrefix(self):
        return self.data.get("prefix")

    def getBlacklistedWords(self):
        return self.data.get("blacklist_words")


    def getCommandData(self, command_name):
        return self._readJSON(self.command_folder+"/"+command_name)

    def getCommandArgDescription(self, command_name, argument):
        res = self.messages.get("args", {}).get(argument, None)
        if res is not None:
            return res

        res = self.getCommandData(command_name).get("args", {}).get(argument, None)
        if res is None:
            return argument +" argument for command "+ command_name+" is not define"
        else:
            return res

    def getCommandRestrictions(self, command_name):
        return self.data.get("command_restriction", {}).get(command_name, {})

    def getCommandEmbeds(self, command: str, message: str):
        res = self.messages.get("embed_format", {}).get(message, None)
        if res is None:
            return self.getCommandData(command).get("embed_format", {}).get(message, None)
        else:
            return res

    def getWarningLevels(self) -> int:
        return self.data.get("warnings", {}).get("warns", 0)

    def getWarningDataForLevel(self, level: int) -> dict:
        return self.data.get("warnings", {}).get("warn-"+str(level), {})


    def getLevelGlobalMax(self) -> int:
        return int(self.data.get("leveling", {}).get("max_levels", 10))
    def getLevelGlobalMin(self) -> int:
        return int(self.data.get("leveling", {}).get("min_levels", 0))

    def getLevelExceptionalRoleMin(self, role_id) -> int | None:
        res: str | None = self.data.get("leveling", {}).get("level_limit_exceptions", {}).get("roles", {}).get(str(role_id), {}).get("min_levels", None)
        if res is None:
            return None
        return int(res)

    def getLevelExceptionalRoleMax(self, role_id) -> int | None:
        res: str | None = self.data.get("leveling", {}).get("level_limit_exceptions", {}).get("roles", {}).get(str(role_id), {}).get("max_levels", None)
        if res is None:
            return None
        return int(res)


    def getLevelExceptionalUserMin(self, user_id) -> int | None:
        res: str | None = self.data.get("leveling", {}).get("level_limit_exceptions", {}).get("users", {}).get(str(user_id), {}).get("min_levels", None)
        if res is None:
            return None
        return int(res)


    def getLevelExceptionalUserMax(self, user_id) -> int | None:
        res: str | None = self.data.get("leveling", {}).get("level_limit_exceptions", {}).get("users", {}).get(str(user_id), {}).get("max_levels", None)
        if res is None:
            return None
        return int(res)



    def getCommandMessages(self, command_name, message) -> list:
        res = self.messages.get("messages", {}).get(message, [])
        if len(res) == 0:
            return self.getCommandData(command_name).get("messages", {}).get(message, [])
        else:
            return res

    def getDMMessages(self, message) -> list:
        return self.messages.get("dm", {}).get(message, [])


    def getCommandActiveMessages(self, command_name) -> list:
        return self.getCommandData(command_name).get("message_names", [])


    def getInvalidMember(self):
        return "Invalid Member"

    def getInvalidRole(self):
        return "Invalid Role"

    def getInvalidChannel(self):
        return "Invalid Channel"

    def getInvalidArg(self):
        return "Invalid Arg"

    def getInvalidChannelKey(self):
        return "invalid_channel"

    def getRestrictedKey(self):
        return "restricted"

    def getInvalidArgsKey(self):
        return "invalid_args"

    def getInvalidMemberKey(self):
        return "invalid_member"

    def getInvalidRoleKey(self):
        return "invalid_role"

    def getMentionMemberKey(self):
        return "mention_member_arg"

    def getDatetimeKey(self):
        return "datetime_arg"

    def getEnterMessageKey(self):
        return "message_arg"

    def getBlacklistWordsKey(self):
        return "blacklist_words_arg"

    def getMemberIDKey(self):
        return "member_id_arg"

    def getMentionRoleKey(self):
        return "mention_role_arg"

    def getNumberKey(self):
        return "number_arg"

    def getMentionVoiceChannelKey(self):
        return "mention_voice_channel_arg"

    def getMentionTestChannelKey(self):
        return "mention_text_channel_arg"

    def getReasonKey(self):
        return "reason_arg"

    def getUnknownErrorKey(self):
        return "unknown_error"

    def getEmbedTitle(self):
        return "title"

    def getEmbedColor(self):
        return "color"

    def getEmbedFooter(self):
        return "footer"

    def getEmbedFooterIconUrl(self):
        return "footer_icon_url"

    def getEmbedImageUrl(self):
        return "image_url"

    def getEmbedDescription(self):
        return "description"

    def getEmbedFields(self):
        return "fields"

    def getEmbedAuthorName(self):
        return "author_name"

    def getEmbedAuthorUrl(self):
        return "author_url"

    def getEmbedAuthorIconUrl(self):
        return "author_icon_url"

    def isActivePlaceholder(self, placeholder: str):
        return placeholder in self.data.get("activated_placeholders")

    def getUsernamePlaceholder(self):
        return "/username/"

    def getRoleNamePlaceholder(self):
        return "/role_name/"

    def getBlacklistWordsPlaceholder(self):
        return "/role_name/"

    def getEphPlaceholder(self):
        return "/eph/"

    def getAvatarUrlPlaceholder(self):
        return "/avatar_url/"

    def getBotLatencyPlaceholder(self):
        return "/bot_latency/"

    def getErrorPlaceholder(self):
        return "/error/"

    def getReasonPlaceholder(self):
        return "/reason/"

    def getDatetimePlaceholder(self):
        return "/datetime/"

    def getInvitePlaceholder(self):
        return "/invite/"

    def getNumberPlaceholder(self):
        return "/number/"

    def getChannelNamePlaceholder(self):
        return "/channel_name/"

    def getMessagePlaceholder(self):
        return "/message/"


"""
    def getBanMemberKey(self):
        return "ban_member"

    def getUnbanMemberKey(self):
        return "unban_member"

    def getAddedRoleKey(self):
        return "add_role"

    def getDeafenKey(self):
        return "deafen_member"

    def getUndeafenKey(self):
        return "undeafen_member"

    def getClearWarningsMemberKey(self):
        return "clear_warinings_member"

    def getInviteKey(self):
        return "invite"

    def getAddedWordsToBlacklistKey(self):
        return "added_words_to_blacklist"

    def getWarnMemberKey(self):
        return "warn_member"

    def getPingKey(self):
        return "ping"

    def wordDescription(self):
        return "description"

    def getViewWarnMembersKey(self):
        return "view_warnings"

    def getKickedMemberKey(self):
        return "kick_member"

    def getRemoveWarningKey(self):
        return "remove_warn"

    def getMoveMemberToChannelKey(self):
        return "move_member_to_channel"

    def getRemoveMessagesKey(self):
        return "removed_messages"

    def getTimeoutMemberKey(self):
        return "timeout_member"

    def getRemoveTimeoutMemberKey(self):
        return "remove_timeout_member"

    def getSlowmodeChannelKey(self):
        return "slowmode_channel"

    def getVoiceMuteMemberKey(self):
        return "voice_muted_member"

    def getMentionMemberKey(self):
        return "mention_member_arg"

    def getVoiceUnmuteMemberKey(self):
        return "voice_unmute_member"

    def getSayMessageKey(self):
        return "say_message"

    def getKickFromVoiceKey(self):
        return "kick_member_from_voice
        
     def getAvatarMessageKey(self):
        return "avatar"
        
        """