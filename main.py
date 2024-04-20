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


# TODO: finish unban

@bot.command()
async def sync(ctx):
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} command(s).")
    await ctx.send(f"Synced {len(synced)} command(s).")


if __name__ == "__main__":
    token = configManager.getBotToken()
    if token is None or len(token.replace(" ", "")) == 0:
        print("You need \"discord_bot_token\" in the config.json to be a valid token")
        exit()

    bot.run(token)
