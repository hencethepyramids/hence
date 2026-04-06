import discord
from discord import app_commands
from discord.ext import commands

from bot.api_client import HenceAPI

STATUS_LABELS = {
    2: "Tribemember",
    1: "Friendly",
    0: "Unknown",
    -1: "Enemy",
    -2: "Enemy (@here)",
    -3: "Enemy (@everyone)",
}

STATUS_CHOICES = [
    app_commands.Choice(name="Tribemember", value=2),
    app_commands.Choice(name="Friendly", value=1),
    app_commands.Choice(name="Unknown", value=0),
    app_commands.Choice(name="Enemy", value=-1),
    app_commands.Choice(name="Enemy + @here", value=-2),
    app_commands.Choice(name="Enemy + @everyone", value=-3),
]


def _format_player_line(player: dict) -> str:
    status = STATUS_LABELS.get(player.get("status", 0), "Unknown")
    tribe = f" | {player['tribe']}" if player.get("tribe") else ""
    return f"Status: {status}{tribe} | Last seen: {player['last_seen'][:10]}"


class SearchCog(commands.Cog):
    def __init__(self, bot: commands.Bot, api: HenceAPI) -> None:
        self.bot = bot
        self.api = api

    @app_commands.command(name="search", description="Search for players by name, tribe, or status")
    @app_commands.describe(
        name="Search by partial or full player name",
        tribe="Search by tribe name",
        status="Search by relationship status",
    )
    @app_commands.choices(status=STATUS_CHOICES)
    async def search(
        self,
        interaction: discord.Interaction,
        name: str | None = None,
        tribe: str | None = None,
        status: int | None = None,
    ) -> None:
        await interaction.response.defer()

        if not name and tribe is None and status is None:
            await interaction.followup.send("Provide at least one of: `name`, `tribe`, or `status`.")
            return

        results: list[dict] = []
        search_type = ""

        if name:
            if len(name.strip()) < 2:
                await interaction.followup.send("Name search must be at least 2 characters.")
                return
            results = await self.api.search_players(name.strip())
            search_type = f'name "{name}"'
        elif tribe is not None:
            if len(tribe.strip()) < 2:
                await interaction.followup.send("Tribe search must be at least 2 characters.")
                return
            results = await self.api.search_by_tribe(tribe.strip())
            search_type = f'tribe "{tribe}"'
        elif status is not None:
            results = await self.api.search_by_status(status)
            search_type = f"status {STATUS_LABELS.get(status, str(status))}"

        if not results:
            await interaction.followup.send(f"No players found for {search_type}.")
            return

        embed = discord.Embed(
            title=f"Search: {search_type} ({len(results)} found)",
            color=discord.Color.blurple(),
        )

        for player in results[:15]:
            eos_short = player["eos_id"][:20] + "…" if len(player["eos_id"]) > 20 else player["eos_id"]
            embed.add_field(
                name=eos_short,
                value=_format_player_line(player),
                inline=False,
            )

        if len(results) > 15:
            embed.set_footer(text=f"Showing 15 of {len(results)} results. Use /whois for full details.")

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot, api: HenceAPI) -> None:
    await bot.add_cog(SearchCog(bot, api))
