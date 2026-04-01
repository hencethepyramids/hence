import logging

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class ReadyCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        logger.info("Logged in as %s (ID: %s)", self.bot.user, self.bot.user.id)
        await self.bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="ARK servers",
            )
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReadyCog(bot))
