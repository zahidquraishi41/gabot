import discord
from discord import app_commands
from discord.ext import commands

from database import AsyncDatabase
from utils import end_giveaway, announce_winner

from typing import Literal


class GiveawayStop(commands.Cog):
    def __init__(self, bot: commands.Bot, db: AsyncDatabase):
        self.bot = bot
        self.db = db

    @app_commands.command(
        name="giveaway_stop", description="Stop an active giveaway early by its ID."
    )
    @app_commands.describe(
        giveaway_id="The ID of the giveaway to stop",
        announce="Whether to announce the winner after stopping. Default: yes",
    )
    async def stop(
        self,
        interaction: discord.Interaction,
        giveaway_id: int,
        announce: Literal["yes", "no"] = "yes",
    ):
        await interaction.response.defer(ephemeral=True)

        # Fetch the giveaway
        giveaway = await self.db.get_giveaway(giveaway_id)
        if not giveaway:
            return await interaction.followup.send(
                f"❌ Giveaway with ID **{giveaway_id}** not found.", ephemeral=True
            )

        # Make sure command is being run in the same guild as the giveaway
        if giveaway.guild_id != interaction.guild.id:
            return await interaction.followup.send(
                "⚠️ This giveaway does not belong to this server.",
                ephemeral=True,
            )

        # Permission check: admin or giveaway creator
        member = interaction.user
        if not (
            member.guild_permissions.administrator or member.id == giveaway.creator_id
        ):
            return await interaction.followup.send(
                "⚠️ Only the giveaway creator or a server administrator can stop this giveaway.",
                ephemeral=True,
            )

        # Check if giveaway is already inactive
        if not giveaway.active:
            return await interaction.followup.send(
                f"⚠️ Giveaway **{giveaway.title}** has already ended.", ephemeral=True
            )

        # Mark giveaway as inactive
        await self.db.set_inactive(giveaway.id)

        # Fetch the channel
        channel = self.bot.get_channel(giveaway.channel_id)
        if channel is None:
            return await interaction.followup.send(
                "⚠️ Could not find the giveaway channel to announce winners. Please notify manually.",
                ephemeral=True,
            )

        # End the giveaway (disable buttons, update embed)
        await end_giveaway(self.bot, self.db, giveaway, channel)
        if announce == "yes":
            await announce_winner(self.db, giveaway, channel)

        await interaction.followup.send(
            f"✅ Giveaway **{giveaway.title}** has been successfully stopped.",
            ephemeral=True,
        )
