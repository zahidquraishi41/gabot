import random

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Bot

from database import AsyncDatabase


class GiveawayReroll(commands.Cog):
    def __init__(self, bot: Bot, db: AsyncDatabase):
        self.bot = bot
        self.db = db

    @app_commands.command(
        name="giveaway_reroll",
        description="Reroll a giveaway by its ID to select new winners.",
    )
    @app_commands.describe(giveaway_id="The ID of the giveaway you want to reroll")
    async def reroll(self, interaction: discord.Interaction, giveaway_id: int):
        await interaction.response.defer(ephemeral=True)

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
                "⚠️ Only the giveaway creator or a server administrator can reroll this giveaway.",
                ephemeral=True,
            )

        # Check if giveaway has ended
        if giveaway.active:
            return await interaction.followup.send(
                f"⚠️ Giveaway **{giveaway.title}** is still active. Wait for it to end before rerolling.",
                ephemeral=True,
            )

        # Get participants
        participants = await self.db.get_participants(giveaway.id)
        if not participants:
            return await interaction.followup.send(
                f"⚠️ No participants joined the giveaway **{giveaway.title}**. Cannot reroll.",
                ephemeral=True,
            )

        # Pick winners
        winners = random.sample(
            participants, k=min(giveaway.winners_count, len(participants))
        )
        winners_mentions = " ".join(f"<@{uid}>" for uid in winners)

        # Clear old winners and store new winners in DB
        await self.db.clear_winners(giveaway.id)
        await self.db.add_winners(giveaway.id, winners)

        # Send announcement in giveaway channel
        channel = self.bot.get_channel(giveaway.channel_id)
        if channel is None:
            return await interaction.followup.send(
                "⚠️ Could not find the giveaway channel to announce new winners. Please notify manually.",
                ephemeral=True,
            )

        await channel.send(
            f"🎉 Giveaway **{giveaway.title}** has been rerolled!\n"
            f"New winner(s): {winners_mentions}\n"
            f"📩 Please DM the host to claim your prize!"
        )

        await interaction.followup.send(
            f"✅ Giveaway **{giveaway.title}** has been successfully rerolled.",
            ephemeral=True,
        )
