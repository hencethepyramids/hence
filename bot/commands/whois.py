import discord
from discord import app_commands
from discord.ext import commands

from bot.api_client import HenceAPI


class WhoisCog(commands.Cog):
    def __init__(self, bot: commands.Bot, api: HenceAPI) -> None:
        self.bot = bot
        self.api = api

    @app_commands.command(name="whois", description="Look up a player by EOS ID")
    @app_commands.describe(eos_id="The player's EOS (Epic Online Services) ID")
    async def whois(self, interaction: discord.Interaction, eos_id: str) -> None:
        await interaction.response.defer()

        player = await self.api.get_player(eos_id.strip())
        if not player:
            await interaction.followup.send(f"No player found with EOS ID `{eos_id}`.")
            return

        aliases = player.get("aliases", [])
        current_name = aliases[-1]["name"] if aliases else "Unknown"

        embed = discord.Embed(
            title=f"Player: {current_name}",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="EOS ID", value=f"`{player['eos_id']}`", inline=False)
        embed.add_field(name="Steam ID", value=player.get("steam_id") or "—", inline=True)
        embed.add_field(name="Total Sessions", value=str(player["total_sessions"]), inline=True)
        embed.add_field(name="First Seen", value=player["first_seen"][:10], inline=True)
        embed.add_field(name="Last Seen", value=player["last_seen"][:10], inline=True)

        if aliases:
            names = [a["name"] for a in aliases]
            # Show most recent 10 names
            display = "\n".join(f"• {n}" for n in names[-10:])
            if len(names) > 10:
                display = f"*(showing last 10 of {len(names)})*\n" + display
            embed.add_field(name="Known Names", value=display, inline=False)

        if player.get("notes"):
            embed.add_field(name="Admin Notes", value=player["notes"], inline=False)

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot, api: HenceAPI) -> None:
    await bot.add_cog(WhoisCog(bot, api))
