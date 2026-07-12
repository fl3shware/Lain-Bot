import asyncio
import os
 
import discord
from discord.ext import commands
 
import config
 
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=config.COMMAND_PREFIX, intents=intents)
 
INITIAL_EXTENSIONS = [
    "cogs.events",
    "cogs.xp",
]
 
 
async def main():
    async with bot:
        for extension in INITIAL_EXTENSIONS:
            await bot.load_extension(extension)
        # Add token
        await bot.start("BOT_TOKEN")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nLeaving the wired\n")
