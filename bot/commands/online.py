import discord
from discord import app_commands
from discord.ext import commands

from bot.api_client import HenceAPI


class OnlineCog(commands.Cog):
    def __init__(self, bot: commands.Bot, api: HenceAPI) -> None:
        self.bot = bot
        self.api = api

    @app_commands.command(name="online", description="List all players currently online across tracked servers")
    async def online(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()

        players = await self.api.get_online_players()

        if not players:
            await interaction.followup.send("No players currently online on any tracked server.")
            return

        # Group by server
        by_server: dict[str, list[dict]] = {}
        for p in players:
            by_server.setdefault(p["server_name"], []).append(p)

        embed = discord.Embed(
            title=f"Online Players — {len(players)} total",
            color=discord.Color.green(),
        )

        for server_name, server_players in sorted(by_server.items()):
            lines = []
            for p in server_players:
                eos_short = p["eos_id"][:12] + "…" if len(p["eos_id"]) > 12 else p["eos_id"]
                lines.append(f"`{eos_short}` {p['current_name']}")
            embed.add_field(
                name=f"{server_name} ({len(server_players)})",
                value="\n".join(lines),
                inline=False,
            )

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot, api: HenceAPI) -> None:
    await bot.add_cog(OnlineCog(bot, api))
