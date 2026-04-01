import asyncio
import logging

import discord
from discord.ext import commands

from bot.api_client import HenceAPI
from bot.commands.online import OnlineCog
from bot.commands.search import SearchCog
from bot.commands.whois import WhoisCog
from bot.config import settings
from bot.events.on_ready import ReadyCog

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class HenceBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.api = HenceAPI()

    async def setup_hook(self) -> None:
        await self.add_cog(ReadyCog(self))
        await self.add_cog(WhoisCog(self, self.api))
        await self.add_cog(OnlineCog(self, self.api))
        await self.add_cog(SearchCog(self, self.api))

        guild = discord.Object(id=settings.discord_guild_id)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        logger.info("Slash commands synced to guild %s", settings.discord_guild_id)

    async def close(self) -> None:
        await self.api.aclose()
        await super().close()


async def main() -> None:
    bot = HenceBot()
    async with bot:
        await bot.start(settings.discord_token)


if __name__ == "__main__":
    asyncio.run(main())
