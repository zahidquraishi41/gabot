import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import utcnow

from database import AsyncDatabase
from giveaway import Giveaway
from utils import parse_duration, post_giveaway

from typing import Literal


class GiveawayCreate(commands.Cog):
    def __init__(self, bot: commands.Bot, db: AsyncDatabase):
        self.bot = bot
        self.db = db

    @app_commands.command(name="giveaway_create", description="Create a giveaway")
    @app_commands.describe(
        title="Title of the giveaway. Default: 'Giveaway'",
        prize="The prize being given away. Default: 'Surprise!'",
        winners_count="Number of winners to pick. Default: 1",
        ends="When the giveaway ends (e.g., 1d, 2h30m, 45s). Default: 1d",
        required_role="Role required to participate. Default: everyone",
        ping_role="Whether to ping the required role when the giveaway starts. Default: no",
        channel="Channel where the giveaway will be posted. Default: current channel",
        host="User hosting the giveaway. Default: You",
        recurring="Should the giveaway repeat automatically after it ends? Default: no",
        criteria="Participation criteria to display in the giveaway. Note: the bot does not enforce this; users are responsible for following it. Default: None",
    )
    async def giveaway_create(
        self,
        interaction: discord.Interaction,
        title: str = "Giveaway",
        prize: str = "Surprise!",
        winners_count: int = 1,
        ends: str = "1d",
        required_role: discord.Role = None,
        ping_role: Literal["yes", "no"] = "no",
        channel: discord.TextChannel = None,
        host: discord.Member = None,
        recurring: Literal["yes", "no"] = "no",
        criteria: str = None,
    ):
        await interaction.response.defer(ephemeral=True)
        channel = channel or interaction.channel
        host_id = host.id if host else None
        role_id = required_role.id if required_role else None
        created_at = int(utcnow().timestamp())
        try:
            ends_at = parse_duration(ends)
        except Exception:
            return await interaction.followup.send(
                "❌ Invalid duration format. Please use something like '1d 2h 3m 4s'.",
                ephemeral=True,
            )

        await post_giveaway(
            self.bot,
            self.db,
            Giveaway(
                None,
                interaction.guild.id,
                channel.id,
                None,
                title,
                prize,
                criteria,
                winners_count,
                created_at,
                created_at + ends_at,
                interaction.user.id,
                host_id,
                role_id,
                int(ping_role == "yes"),
                int(recurring == "yes"),
                1,
            ),
        )
        await interaction.followup.send(
            f"🎉 Giveaway **{title}** has started in {channel.mention}!", ephemeral=True
        )
