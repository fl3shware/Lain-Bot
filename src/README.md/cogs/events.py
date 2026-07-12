import discord
from discord.ext import commands


class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Logged in as {self.bot.user}")
        await self.bot.change_presence(
            activity=discord.Game(name="=help for more information"),
            status=discord.Status.idle,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))
