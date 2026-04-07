import logging

import discord
from discord import app_commands
from discord.ext import commands

from bot.api_client import HenceAPI
from bot.config import settings

logger = logging.getLogger(__name__)

STATUS_LABELS = {
    2: "Tribemember",
    1: "Friendly",
    0: "Unknown",
    -1: "Enemy",
    -2: "Enemy (@here)",
    -3: "Enemy (@everyone)",
}

STATUS_COLORS = {
    2: discord.Color.blue(),
    1: discord.Color.green(),
    0: discord.Color.light_grey(),
    -1: discord.Color.red(),
    -2: discord.Color.red(),
    -3: discord.Color.red(),
}


class ReportCog(commands.Cog):
    def __init__(self, bot: commands.Bot, api: HenceAPI) -> None:
        self.bot = bot
        self.api = api

    @app_commands.command(name="report", description="Log a player sighting on a server")
    @app_commands.describe(
        eos_id="Player's EOS (Epic Online Services) ID",
        server="Server name where the player was spotted",
    )
    async def report(
        self,
        interaction: discord.Interaction,
        eos_id: str,
        server: str,
    ) -> None:
        await interaction.response.defer()

        reporter_id = str(interaction.user.id)
        reporter_name = interaction.user.display_name

        sighting = await self.api.report_sighting(
            eos_id=eos_id.strip(),
            server_name=server.strip(),
            reported_by_discord_id=reporter_id,
            reported_by_name=reporter_name,
        )

        if sighting is None:
            await interaction.followup.send(
                f"Player with EOS ID `{eos_id}` not found. Use `/add` first."
            )
            return

        player = await self.api.get_player(eos_id.strip())
        if not player:
            await interaction.followup.send("Sighting recorded, but could not fetch player details.")
            return

        status = player.get("status", 0)
        status_label = STATUS_LABELS.get(status, str(status))
        aliases = player.get("aliases", [])
        name = aliases[-1]["name"] if aliases else "Unknown"

        embed = discord.Embed(
            title="Sighting Recorded",
            color=STATUS_COLORS.get(status, discord.Color.light_grey()),
        )
        embed.add_field(name="Player", value=name, inline=True)
        embed.add_field(name="Status", value=status_label, inline=True)
        embed.add_field(name="Server", value=server, inline=True)
        embed.add_field(name="EOS ID", value=f"`{eos_id}`", inline=False)
        if player.get("tribe"):
            embed.add_field(name="Tribe", value=player["tribe"], inline=True)
        embed.set_footer(text=f"Reported by {reporter_name}")

        await interaction.followup.send(embed=embed)

        # Post alert to #ark-alerts if enemy status
        if status <= -1:
            await self._send_alert(interaction, player, name, status, server, eos_id)

    async def _send_alert(
        self,
        interaction: discord.Interaction,
        player: dict,
        name: str,
        status: int,
        server: str,
        eos_id: str,
    ) -> None:
        guild = interaction.guild
        if not guild:
            return

        channel = discord.utils.get(guild.text_channels, name=settings.alerts_channel_name)
        if not channel:
            logger.warning("Alerts channel '%s' not found", settings.alerts_channel_name)
            return

        status_label = STATUS_LABELS.get(status, str(status))

        ping = ""
        if status == -3:
            ping = "@everyone "
        elif status == -2:
            ping = "@here "

        embed = discord.Embed(
            title=f"Enemy Spotted: {name}",
            color=discord.Color.red(),
        )
        embed.add_field(name="EOS ID", value=f"`{eos_id}`", inline=False)
        embed.add_field(name="Status", value=status_label, inline=True)
        embed.add_field(name="Server", value=server, inline=True)
        if player.get("tribe"):
            embed.add_field(name="Tribe", value=player["tribe"], inline=True)
        if player.get("notes"):
            embed.add_field(name="Notes", value=player["notes"], inline=False)
        embed.set_footer(text=f"Reported by {interaction.user.display_name}")

        # Use allowed_mentions to make the ping actually trigger notifications
        allowed = discord.AllowedMentions(everyone=(status <= -2))
        await channel.send(content=ping if ping else None, embed=embed, allowed_mentions=allowed)
