import os, sys

import cogs.ext.utils.utils as utils
import cogs.ext.messages as messages

"""
- ``0x<hex>``
        - ``#<hex>``
        - ``0x#<hex>``
        - ``rgb(<number>, <number>, <number>)``
"""

"""
@app_commands.choices(color=[Choice(name="🔴 Red", value=0xff0000),
                Choice(name="🔵 Blue", value=0x0000ff),
                Choice(name="🟢 Green", value=0x00ff00),
                Choice(name="🟣 Purple", value=0x883af1),
                Choice(name="🟡 Yellow", value=0xffe34d),
                Choice(name="🟠 Orange", value=0xff8000),
                Choice(name="🟤 Brown", value=0x845321),
                Choice(name="⚫️ Black", value=0xffffff),
                Choice(name="⚪️ White", value=0x000000),
                ])

"""

# @app_commands.checks.has_permissions(administrator=True)

try:
    import discord
    from discord.ext import commands
except ImportError:
    if sys.platform.startswith('win'):
        os.system("python -m pip install discord.py")
    else:
        os.system("python3 -m pip install discord.py")
    try:
        import discord
        from discord.ext import commands
    except ImportError:
        print("Can't import discord.py! Try to install it.")
        exit()

bot = commands.Bot(command_prefix=utils.configManager.getBotPrefix(), intents=discord.Intents.all())


def FindAll(directory: str, extension: str = ".py", exclusions: list = ["__init__.py"]) -> list:
    """
    Finds all cogs within a certain directory, excluding everything that matches exclusions

    Arguments
    ~~~~~~~~~

    `REQUIRED` directory: str
        Location to look for cog files

    `OPTIONAL` extension: str
        Ending of a file to be considered a cog
        (defaults to `.py`)

    `OPTIONAL` exclusions: Union[List[str], str]
        exlusions that will be ignored as cog files
        (defaults to ["__init__.py"])

    """

    # Convert Exclusions to a list if its a string.
    if isinstance(exclusions, str):
        exclusions = [exclusions]

    cog_locations = []
    for root, _, files in os.walk(directory):
        for file in files:
            file: str
            if not isinstance(file, str):
                continue
            if not file.endswith(extension) or file in exclusions or root in exclusions:
                continue

            cog_locations.append(
                os.path.relpath(os.path.join(root, file), os.getcwd())
                .replace("\\", ".").replace(extension, "").replace("/", "."))

    return cog_locations


@bot.event
async def on_ready():
    for loc in FindAll("cogs", exclusions=["__init__.py", "cogs\\ext", "cogs\\ext\\utils", "moderator_cog.py"]):
        await bot.load_extension(name=loc)
    print('Bot:', bot.user.name)
    res = await messages.handleMessage(bot, "on_ready", "on_ready",
                                       placeholders={utils.configManager.getUsernamePlaceholder(): bot.user.name,
                                                     utils.configManager.getNumberPlaceholder(): bot.user.id},
                                       interaction=None, ctx=None)


@bot.command()
async def sync(ctx):
    if await messages.isCommandRestricted(bot, "sync", "sync",
                                          interaction=None, ctx=ctx):
        return
    synced = await bot.tree.sync()
    res = await messages.handleMessage(bot, "sync", "sync",
                                       placeholders={utils.configManager.getNumberPlaceholder(): str(len(synced))},
                                       interaction=None, DMUser=None, ctx=ctx)


@bot.command()
async def reload(ctx: discord.ext.commands.context.Context):
    if await messages.isCommandRestricted(bot, "reload", "reload", interaction=None,
                                          ctx=ctx):
        return

    utils.configManager.reloadConfig()
    res = await messages.handleMessage(bot, "reload", "reload",
                                       placeholders={},
                                       interaction=None, DMUser=None, ctx=ctx)


if __name__ == "__main__":
    token = utils.configManager.getBotToken()
    if token is None or len(token.replace(" ", "")) == 0:
        print("You need \"discord_bot_token\" in the config.json to be a valid token")
        exit()

    bot.run(token)

# TODO LIST
# + add documentation at the end of the project
# + add actions that gets data: create backups, load backups, gets url data, built-in webscraper, get message history, get members, get banned members, get roles, get channels, get categories, get emojis, get stickers
# + add youtube music player
# + add custom commands (application/prefix)
# + add custom events (on_member_voice_update..., custom conditions, custom actions based on them)
# + add action to execute in time like every 5 seconds (make it very customizable)
# + add option for custom cogs to be added
# + add webhook support
# + add emoji reactions
# + add stickers
# + continue with guild actions

"""

Actions
"permissions": {"roles": [{"role_id": "916359207010312242", "permissions": {"send_messages": true} }]},
"commands": [
    {
    'command': 'mycommand',
    'args': ['azazazaza'],
    'type': 'app'
    }
]

"messages": {
    "avatar:mymessage": ["Error /error_path/"]
}


"embed_format": {
    "avatar": {
      "title": "/username/",
      "color": "random",
      "description": "",
      "footer": "",
      "footer_icon_url": "",
      "image_url": "/avatar_url/",
      "author_name": "Override",
      "author_url": "",
      "author_icon_url": "",
      "fields": {"":  ""}
    }
  },

"args": {
    "mention_member_arg": "Mention member",
    "datetime_arg": "Mention member",
    "mention_role_arg": "Mention role",
    "message_arg": "Enter a message",
    "reason_arg": "Give a reason",
    "number_arg": "Give a number",
    "invalid_args": "Invalid arguments /eph/",
    "blacklist_words_arg": "Give some words seperated by comma",
    "mention_voice_channel_arg": "Mention a voice channel",
    "mention_text_channel_arg": "Mention a text channel",
    "member_id_arg": "Give member id"

  },

  "messages": {
  
  invalid_channel
  
    "avatar": "Hello",
    "invalid_member": "No such member",
    "added_words_to_blacklist": "You added /blacklist_words/ to blacklist",
    "invalid_role": "No such role",
    "add_role": "Added role /role_name/",
    "unknown_error": "Error! /error/",
    "warn_member": "You warned /username/ for /reason/",
    "view_warnings": "/username/ -> /reason/",
    "remove_warn": "You removed warning from /username/",
    "deafen_member": "You deafened /username/ for /reason/",
    "undeafen_member": "You undeafened /username/ for /reason/",
    "clear_warinings_member": "You cleared warnings for /username/ for /reason/",
    "invite": "/invite/",
    "kick_member": "You kicked /username/ for /reason/",
    "move_member_to_channel": "You moved /username/ to /channel_name/",
    "ban_member": "You banned /username/ reason: /reason/",
    "unban_member": "You unbanned /username/",
    "ping": "Pong /bot_latency/",
    "removed_messages": "removed /number/ messages",
    "say_message": "/message/",
    "timeout_member": "You timeout /username/ for /reason/ until /datetime/",
    "remove_timeout_member": "You removed timeout from /username/",
    "slowmode_channel": "You activated slowmode for /channe_name/ with /number/ seconds",
    "voice_muted_member": "You muted /username/",
    "voice_unmute_member": "You unmuted /username/",
    "kick_member_from_voice": "You kicked /username/"

  }


 Because of Discord limitations I can't delete messages past 2 weeks.

 If you want to clear a whole channel just right-click the channel then select "Clone Channel"


"command_restriction": {
    "avatar": {"roles_id":  {"reason": "", "status": [1111]}, "users_id": {"reason": "", "status": [3131]}, 
    "channels_id":  {"reason": "", "status": [123131]}},
    "say": {"all": {"reason": "", "status": false}}
  },


command_permissions -> who can use what command and where?

key -> command name
value -> dict data
 |-> "any_roles_id": list of role ids that the user MUST have at least one to use this command 
 |-> "all_roles_id": list of role ids that the user MUST have all of them to use this command 
 |-> "users_id": list of users that can use this command
 |-> "channels_id": list of channels that this command can be only be used in
 |-> "all": Should the command be allowed for everyone or be restricted | true -> everyone . false -> restricted
 

"""
