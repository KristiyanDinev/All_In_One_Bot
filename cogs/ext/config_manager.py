from __future__ import annotations
import random, os, json


class ConfigManager:
    def __init__(self, configPath, messagesConfigPath, warningsConfigPath, commandsFolderPath, levelConfigPath):
        self.config_path = configPath
        self.message_path = messagesConfigPath
        self.warning_path = warningsConfigPath
        self.command_folder = commandsFolderPath
        self.levels_path = levelConfigPath
        self.levelsData = self._readJSON(levelConfigPath)
        self.warningsData = self._readJSON(warningsConfigPath)
        self.configData = self._readJSON(configPath)
        self.messagesData = self._readJSON(messagesConfigPath)

    def saveLevelJSON(self) -> None:
        self._saveJSON(self.levels_path, self.levelsData)

    def saveCommandJSON(self, command: str, command_data: dict) -> None:
        self._saveJSON(self.command_folder + "/" + command + ".json", command_data)

    def saveConfigJSON(self) -> None:
        self._saveJSON(self.config_path, self.configData)

    def saveWarningsJSON(self) -> None:
        self._saveJSON(self.warning_path, self.warningsData)

    def saveMessagesJSON(self) -> None:
        self._saveJSON(self.message_path, self.messagesData)

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
        self.warningsData = self._readJSON(self.warning_path)
        self.configData = self._readJSON(self.config_path)
        self.messagesData = self._readJSON(self.message_path)

    def getRoleManagements(self) -> list:
        res = self.configData.get("role_management", {})
        if not isinstance(res, dict):
            return []
        return list(res.keys())

    def getAllRolesIDByRoleManager(self, manager: str) -> list:
        res = self.__handleMaps(self.configData.get("role_management", {}))
        res = self.__handleMaps(res.get(manager, {})).get("all_roles_id", [])
        if not isinstance(res, list):
            res = []
        return res

    def getAnyRolesIDByRoleManager(self, manager: str) -> list:
        res = self.__handleMaps(self.configData.get("role_management", {}))
        res = self.__handleMaps(res.get(manager, {}))
        res = res.get("any_roles_id", [])
        if not isinstance(res, list):
            return []
        return res

    def getActionData(self, action: str) -> dict:
        return self.__handleMaps(self.__handleMaps(self.configData.get("actions", {})).get(action, {}))

    def getActions(self, combined: str) -> list:
        comb = combined.split(" ")
        res = self.__handleMaps(self.messagesData.get("views", {}))
        res = self.__handleMaps(res.get(comb[0], {}))
        res = self.__handleMaps(res.get(comb[1], {})).get("actions", [])
        if not isinstance(res, list):
            return []
        return list(res)

    def getButtonsByView(self, view: str) -> list:
        res = self.__handleMaps(self.messagesData.get("views", {}))
        res = self.__handleMaps(res.get(view, {}))
        if len(res.keys()) == 0:
            return []
        res.pop("timeout")
        return list(res.keys())

    def getButtonStyle(self, combined: str) -> str:
        comb = combined.split(" ")
        res = self.__handleMaps(self.messagesData.get("views", {}))
        res = self.__handleMaps(res.get(comb[0], {}))
        res = self.__handleMaps(res.get(comb[1], {}))
        return str(res.get("style", "green"))

    def getButtonTimeout(self, view: str) -> float | None:
        res = self.__handleMaps(self.messagesData.get("views", {}))
        res = self.__handleMaps(res.get(view, {}))
        res = res.get("timeout", None)
        if not isinstance(res, int) or not isinstance(res, float):
            return None
        return res

    def getButtonCustomID(self, combined: str) -> str:
        comb = combined.split(" ")
        res = self.__handleMaps(self.messagesData.get("views", {}))
        res = self.__handleMaps(res.get(comb[0], {}))
        res = self.__handleMaps(res.get(comb[1], {}))
        return str(res.get("custom_id", str(random.randint(1, 1000))))

    def getCogData(self) -> dict:
        return self.__handleMaps(self.configData.get('cog_data', {}))

    def getBotToken(self) -> str:
        return str(self.configData.get("discord_bot_token", ""))

    def getBotPrefix(self) -> str:
        return str(self.configData.get("prefix", "!!!"))

    def getCogActiveStatus(self) -> str:
        return str(self.messagesData.get("cog_acticated_status", "loaded"))

    def getCogDeactiveStatus(self) -> str:
        return str(self.messagesData.get("cog_deactivated_status", "unloaded"))

    def getCogNotFoundStatus(self) -> str:
        return str(self.messagesData.get("cog_not_found_status", "not found"))

    def hasButton(self, name: str) -> bool:
        return self.__handleMaps(self.messagesData.get("views", {})).get(name, None) is not None

    def getButtonText(self, name: str) -> str:
        res = self.__handleMaps(self.messagesData.get("views", {}))
        res = self.__handleMaps(res.get(name, {}))
        return str(res.get("label", "No label for " + name))

    def __handleMaps(self, res) -> dict:
        if not isinstance(res, dict):
            return dict()
        return res

    def getButtonStyle(self, name: str) -> str:
        res = self.__handleMaps(self.messagesData.get("views", {}))
        res = self.__handleMaps(res.get(name, {}))
        return str(res.get("style", "green"))

    def getBlacklistedWords(self) -> list:
        return self.configData.get("blacklist_words", [])

    def updateBlacklistWords(self, words: list):
        try:
            self.configData["blacklist_words"] = words
        except Exception as e:
            print(e)
            pass

    def getCommandData(self, command_name):
        return self._readJSON(self.command_folder + "/" + command_name)

    def getCommandArgDescription(self, command_name, argument) -> str:
        res = self.messagesData.get("args", {}).get(argument, None)
        if res is not None:
            return str(res)

        res = self.getCommandData(command_name).get("args", {}).get(argument, None)
        if res is None:
            return argument + " argument for command " + command_name + " is not define"
        else:
            return str(res)

    def getCommandRestrictions(self, command_name) -> dict:
        return dict(self.configData.get("command_restriction", {}).get(command_name, {}))

    def getCommandEmbeds(self, command: str, message: str) -> dict | None:
        res = self.messagesData.get("embed_format", {}).get(message, None)
        if res is None:
            return self.getCommandData(command).get("embed_format", {}).get(message, None)
        else:
            return res

    def getMessagesByChannel(self, name: str) -> list:
        res = self.__handleMaps(self.messagesData.get("channel_messages", {}))
        res = self.__handleMaps(res.get(name, {}))
        res = res.get("messages", [])
        if not isinstance(res, list):
            return []
        return res

    def getEmbedsByChannel(self, name: str) -> list:
        res = self.__handleMaps(self.messagesData.get("channel_messages", {}))
        res = self.__handleMaps(res.get(name, {}))
        res = res.get("embeds", [])
        if not isinstance(res, list):
            return []
        return res

    def getButtonsByChannel(self, name: str) -> list:
        res = self.__handleMaps(self.messagesData.get("channel_messages", {}))
        res = self.__handleMaps(res.get(name, {}))
        res = res.get("views", [])
        if not isinstance(res, list):
            return []
        return res

    def getChannelIdByName(self, name: str) -> int:
        res = self.__handleMaps(self.configData.get("channels", {}))
        res = res.get(name, 0)
        if not isinstance(res, int):
            return 0
        return res

    def getWarningLevels(self) -> int:
        res = self.__handleMaps(self.configData.get("warnings", {}))
        res = res.get("warns", 0)
        if not isinstance(res, int):
            return 0
        return res

    def getWarningDataForLevel(self, level: int) -> dict:
        return self.__handleMaps(self.__handleMaps(self.configData.get("warnings", {})).get("warn-" + str(level), {}))

    def getLevelGlobalMax(self) -> int:
        res = self.__handleMaps(self.configData.get("leveling", {})).get("max_levels", 10)
        if not isinstance(res, int):
            return 10
        return res

    def getLevelGlobalMin(self) -> int:
        res = self.__handleMaps(self.configData.get("leveling", {})).get("min_levels", 0)
        if not isinstance(res, int):
            return 0
        return res

    def getUserLevel(self, user_id) -> int:
        res = self.__handleMaps(self.levelsData.get(str(user_id), {})).get("level", 0)
        if not isinstance(res, int):
            return 0
        return res

    def getUserXP(self, user_id) -> int:
        res = self.__handleMaps(self.levelsData.get(str(user_id), {})).get("xp", 0)
        if not isinstance(res, int):
            return 0
        return res

    def setUserLevel(self, user_id, level) -> None:
        try:
            user_id_str = str(user_id)
            if user_id_str in self.levelsData.keys():
                self.levelsData[user_id_str]["level"] = int(level)
            else:
                self.levelsData[user_id_str] = {"xp": self.getLevelXP(level), "level": int(level)}
        except Exception as e:
            print(e)
            pass

    def setUserXP(self, user_id, xp) -> None:
        try:
            user_id_str = str(user_id)
            if user_id_str in self.levelsData.keys():
                self.levelsData[user_id_str]["xp"] = float(str(round(xp, 2)))
            else:
                self.levelsData[user_id_str] = {"xp": float(str(round(xp, 2))), "level": self.getUserLevel(user_id)}
        except Exception as e:
            print(e)
            pass

    def getLevelExceptionalRoleMin(self, role_id) -> int | None:
        res = self.__handleMaps(self.configData.get("leveling", {}))
        res = self.__handleMaps(res.get("level_limit_exceptions", {}))
        res = self.__handleMaps(res.get("roles", {}))
        res = self.__handleMaps(res.get(str(role_id), {}))
        res = res.get("min_levels", None)
        if not isinstance(res, int):
            return None
        return res

    def getLevelExceptionalRoleMax(self, role_id) -> int | None:
        res = self.__handleMaps(self.configData.get("leveling", {}))
        res = self.__handleMaps(res.get("level_limit_exceptions", {}))
        res = self.__handleMaps(res.get("roles", {}))
        res = self.__handleMaps(res.get(str(role_id)))
        res = res.get("max_levels", None)
        if not isinstance(res, int):
            return None
        return res

    def getLevelExceptionalUserMin(self, user_id) -> int | None:
        res = self.__handleMaps(self.configData.get("leveling", {}))
        res = self.__handleMaps(res.get("level_limit_exceptions", {}))
        res = self.__handleMaps(res.get("users", {}))
        res = self.__handleMaps(res.get(str(user_id), {}))
        res = res.get("min_levels", None)
        if not isinstance(res, int):
            return None
        return res

    def getLevelExceptionalUserMax(self, user_id) -> int | None:
        res = self.__handleMaps(self.configData.get("leveling", {}))
        res = self.__handleMaps(res.get("level_limit_exceptions", {}))
        res = self.__handleMaps(res.get("users", {}))
        res = self.__handleMaps(res.get(str(user_id), {}))
        res = res.get("max_levels", None)
        if not isinstance(res, int):
            return None
        return res

    def getXPPerMessages(self) -> int:
        res = self.__handleMaps(self.configData.get("leveling", {})).get("give_xp_per_messages", 1)
        if not isinstance(res, int):
            return 1
        return res

    def allLevels(self) -> int:
        res = self.__handleMaps(self.configData.get("leveling", {})).get("levels", 999999999)
        if not isinstance(res, int):
            return 999999999
        return res

    def getLevelupXPMultiplier(self) -> float:
        res = self.__handleMaps(self.configData.get("leveling", {}))
        res = res.get("required_xp_for_levelup_multiplier", 4)
        if not isinstance(res, int):
            res = 4
        return float(str(round(res, 2)))

    def getLevelXP(self, level) -> float:
        res = self.__handleMaps(self.configData.get("leveling", {}))
        res = self.__handleMaps(res.get("leveling", {}))
        default = int(level) * self.getLevelupXPMultiplier()
        res = res.get("level-" + str(level), default)
        if not isinstance(res, float) or not isinstance(res, int):
            return float(str(round(default, 2)))
        return float(str(round(res, 2)))

    def getCommandMessages(self, command_name, message) -> list:
        res = self.__handleMaps(self.messagesData.get("messages", {})).get(message, [])
        if not isinstance(res, list):
            res = []
        if len(res) == 0:
            res = self.__handleMaps(self.getCommandData(command_name).get("messages", {})).get(message, [])
            return [] if not isinstance(res, list) else res
        else:
            return res

    def getDMMessages(self, message) -> list:
        res = self.__handleMaps(self.__handleMaps(self.messagesData.get("dm", {}))
                                .get(message, {})).get("messages", [])
        if not isinstance(res, list):
            return []
        return res

    def getDMEmbeds(self, message) -> list:
        res = self.__handleMaps(self.messagesData.get("dm", {}))
        res = self.__handleMaps(res.get(message, {})).get("embeds", [])
        if not isinstance(res, list):
            return []
        return res

    def getDMViews(self, message) -> list:
        res = self.__handleMaps(self.messagesData.get("dm", {}))
        res = self.__handleMaps(res.get(message, {}))
        res = res.get("views", [])
        if not isinstance(res, list):
            return []
        return res

    def getCommandActiveMessages(self, command_name) -> list:
        res = self.getCommandData(command_name).get("message_names", [])
        return res if isinstance(res, list) else []

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
        return placeholder in self.configData.get("activated_placeholders")

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

    def getReasonPlaceholder(self):
        return "/reason/"

    def getNotInLinePlaceholder(self):
        return "/notinline/"

    def getIDPlaceholder(self):
        return "/id/"

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

    def getLevelPlaceholder(self):
        return "/level/"

    def getXPPlaceholder(self):
        return "/xp/"

    def getInvalidUsernamePlaceholder(self):
        return "/invalid_username/"

    def getInvalidRolePlaceholder(self):
        return "/invalid_role/"

    def getInvalidArgumentPlaceholder(self):
        return "/invalid_argument/"

    def getInvalidChannelPlaceholder(self):
        return "/invalid_channel/"

    def getActionPathPlaceholder(self):
        return "/action:path/"

    def getErrorPlaceholder(self):
        return '/error/'

    def getErrorPathPlaceholder(self):
        return '/error/'


