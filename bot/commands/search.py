import discord
from discord import app_commands
from discord.ext import commands

from bot.api_client import HenceAPI


class SearchCog(commands.Cog):
    def __init__(self, bot: commands.Bot, api: HenceAPI) -> None:
        self.bot = bot
        self.api = api

    @app_commands.command(name="search", description="Search for players by partial name")
    @app_commands.describe(name="Partial or full player name to search for")
    async def search(self, interaction: discord.Interaction, name: str) -> None:
        await interaction.response.defer()

        if len(name.strip()) < 2:
            await interaction.followup.send("Search query must be at least 2 characters.")
            return

        results = await self.api.search_players(name.strip())

        if not results:
            await interaction.followup.send(f'No players found matching `{name}`.')
            return

        embed = discord.Embed(
            title=f'Search results for "{name}" ({len(results)} found)',
            color=discord.Color.blurple(),
        )

        for player in results[:10]:
            eos_short = player["eos_id"][:16] + "…" if len(player["eos_id"]) > 16 else player["eos_id"]
            embed.add_field(
                name=eos_short,
                value=f"Sessions: {player['total_sessions']} | Last seen: {player['last_seen'][:10]}",
                inline=False,
            )

        if len(results) > 10:
            embed.set_footer(text=f"Showing 10 of {len(results)} results. Use /whois for full details.")

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot, api: HenceAPI) -> None:
    await bot.add_cog(SearchCog(bot, api))
