import discord
from discord import app_commands
from discord.ext import commands

from bot.api_client import HenceAPI


class HistoryCog(commands.Cog):
    def __init__(self, bot: commands.Bot, api: HenceAPI) -> None:
        self.bot = bot
        self.api = api

    @app_commands.command(name="history", description="View sighting history for a player")
    @app_commands.describe(
        eos_id="Player's EOS (Epic Online Services) ID",
        limit="Number of sightings to show (default 10, max 25)",
    )
    async def history(
        self,
        interaction: discord.Interaction,
        eos_id: str,
        limit: int = 10,
    ) -> None:
        await interaction.response.defer()

        limit = min(max(limit, 1), 25)
        player = await self.api.get_player(eos_id.strip())
        if not player:
            await interaction.followup.send(f"No player found with EOS ID `{eos_id}`.")
            return

        sightings = await self.api.get_player_sightings(eos_id.strip(), limit=limit)

        aliases = player.get("aliases", [])
        name = aliases[-1]["name"] if aliases else "Unknown"

        embed = discord.Embed(
            title=f"Sighting History: {name}",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="EOS ID", value=f"`{player['eos_id']}`", inline=False)

        if not sightings:
            embed.description = "No sightings recorded yet."
        else:
            lines = []
            for s in sightings:
                date = s["seen_at"][:10]
                lines.append(f"• **{s['server_name']}** — {date} (by {s['reported_by_name']})")
            embed.description = "\n".join(lines)

        await interaction.followup.send(embed=embed)
