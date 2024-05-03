import os
import sys

from cogs.ext.utils import *

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
except ImportError:
    if sys.platform.startswith('win'):
        os.system("python -m pip install discord.py")
    else:
        os.system("python3 -m pip install discord.py")
    try:
        import discord
    except ImportError:
        print("Can't import discord.py! Try to install it.")
        exit()

import discord
from discord.ext import commands

bot = commands.Bot(command_prefix=configManager.getBotPrefix(), intents=discord.Intents.all())


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

            if not file.endswith(extension) or file in exclusions:
                continue

            cog_locations.append(
                os.path.relpath(os.path.join(root, file), os.getcwd())
                .replace("\\", ".").replace(extension, "").replace("/", "."))

    return cog_locations


@bot.event
async def on_ready():
    for loc in FindAll("cogs"):
        await bot.load_extension(name=loc)
    print('Bot:', bot.user.name)
    await handleMessageCtx(bot, None, "on_ready",
                           placeholders={configManager.getUsernamePlaceholder(): bot.user.name,
                                         configManager.getNumberPlaceholder(): bot.user.id})


@bot.command()
async def sync(ctx):
    if await handleRestrictedCtx(bot, ctx, "sync"):
        return

    synced = await bot.tree.sync()
    await handleMessageCtx(bot, ctx, "sync",
                           placeholders={configManager.getNumberPlaceholder(): str(len(synced))})


@bot.command()
async def reload(ctx: discord.ext.commands.context.Context):
    if await handleRestrictedCtx(bot, ctx, "reload"):
        return

    configManager.reloadConfig()
    await handleMessageCtx(bot, ctx, "reload")


if __name__ == "__main__":
    token = configManager.getBotToken()
    if token is None or len(token.replace(" ", "")) == 0:
        print("You need \"discord_bot_token\" in the config.json to be a valid token")
        exit()

    bot.run(token)

"""
/*
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
*/


"command_restriction": {
    "avatar": {"roles_id":  [1111], "users_id":  [3131], "channels_id":  [123131]},
    "say": {"all": true}
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
