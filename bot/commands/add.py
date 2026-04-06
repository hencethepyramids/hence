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
    app_commands.Choice(name="Enemy + @here alert", value=-2),
    app_commands.Choice(name="Enemy + @everyone alert", value=-3),
]


class AddCog(commands.Cog):
    def __init__(self, bot: commands.Bot, api: HenceAPI) -> None:
        self.bot = bot
        self.api = api

    @app_commands.command(name="add", description="Add a new player or update an existing one by EOS ID")
    @app_commands.describe(
        eos_id="Player's EOS (Epic Online Services) ID",
        name="In-game name (optional)",
        status="Relationship status (default: Unknown)",
        tribe="Tribe name (optional)",
        steam_id="Steam ID (optional)",
        notes="Admin notes (optional)",
    )
    @app_commands.choices(status=STATUS_CHOICES)
    async def add(
        self,
        interaction: discord.Interaction,
        eos_id: str,
        name: str | None = None,
        status: int | None = None,
        tribe: str | None = None,
        steam_id: str | None = None,
        notes: str | None = None,
    ) -> None:
        await interaction.response.defer()

        player = await self.api.upsert_player(
            eos_id=eos_id.strip(),
            name=name.strip() if name else None,
            status=status,
            tribe=tribe.strip() if tribe else None,
            steam_id=steam_id.strip() if steam_id else None,
            notes=notes.strip() if notes else None,
        )

        if not player:
            await interaction.followup.send("Failed to add/update player. Check the API logs.")
            return

        status_label = STATUS_LABELS.get(player["status"], str(player["status"]))
        embed = discord.Embed(
            title="Player Added / Updated",
            color=discord.Color.green(),
        )
        embed.add_field(name="EOS ID", value=f"`{player['eos_id']}`", inline=False)
        if name:
            embed.add_field(name="Name", value=name, inline=True)
        embed.add_field(name="Status", value=status_label, inline=True)
        if player.get("tribe"):
            embed.add_field(name="Tribe", value=player["tribe"], inline=True)
        if player.get("steam_id"):
            embed.add_field(name="Steam ID", value=player["steam_id"], inline=True)
        if player.get("notes"):
            embed.add_field(name="Notes", value=player["notes"], inline=False)

        await interaction.followup.send(embed=embed)
