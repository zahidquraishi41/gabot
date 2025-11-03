import discord
from discord.utils import utcnow

from database import AsyncDatabase
from giveaway import Giveaway


class GiveawayView(discord.ui.View):
    def __init__(self, db: AsyncDatabase, giveaway: Giveaway, participants: int):
        super().__init__(timeout=None)
        self.giveaway = giveaway
        self.db = db

        self.join.custom_id = "join_btn_" + str(giveaway.id)
        self.join.label = f"🎉 {participants}"
        self.participants.custom_id = "participants_btn_" + str(giveaway.id)

    @classmethod
    async def create(cls, db: AsyncDatabase, giveaway: Giveaway):
        """Async factory for creating GiveawayView with DB data."""
        participants = await db.count_participants(giveaway.id)
        return cls(db, giveaway, participants)

    @discord.ui.button(style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        # Check if the channel exists
        channel = interaction.client.get_channel(self.giveaway.channel_id)
        if channel is None:
            return await interaction.followup.send(
                "⚠️ Could not find the giveaway channel. Please contact a moderator.",
                ephemeral=True,
            )

        # Fetch the giveaway message
        if self.giveaway.message_id is None:
            return await interaction.followup.send(
                "⚠️ This giveaway is still being processed. Please try again in a moment.",
                ephemeral=True,
            )
        try:
            msg = await channel.fetch_message(self.giveaway.message_id)
        except discord.NotFound:
            return await interaction.followup.send(
                "⚠️ Giveaway message could not be found. The giveaway may have ended or been removed.",
                ephemeral=True,
            )
        except discord.HTTPException:
            return await interaction.followup.send(
                "⚠️ Failed to fetch the giveaway message. Please try again later.",
                ephemeral=True,
            )

        # Check if giveaway has ended
        if int(utcnow().timestamp()) >= self.giveaway.ends_at:
            button.disabled = True
            await msg.edit(view=self)
            return await interaction.followup.send(
                f"⏰ This giveaway **{self.giveaway.title}** has already ended.",
                ephemeral=True,
            )

        # Check required role
        if self.giveaway.required_role_id:
            role = interaction.guild.get_role(self.giveaway.required_role_id)
            if role and role not in interaction.user.roles:
                return await interaction.followup.send(
                    f"❌ Your entry to **{self.giveaway.title}** has been denied. "
                    "Please review the requirements for this giveaway.",
                    ephemeral=True,
                )

        # Add or remove participant
        participants = await self.db.get_participants(self.giveaway.id)
        if interaction.user.id in participants:
            await self.db.rem_participant(interaction.user.id, self.giveaway.id)
            msg_text = f"❌ You have left the giveaway **{self.giveaway.title}**."
        else:
            await self.db.add_participant(interaction.user.id, self.giveaway.id)
            msg_text = f"✅ Your entry to **{self.giveaway.title}** has been approved!"

        # Update participant count on the button
        participants_count = await self.db.count_participants(self.giveaway.id)
        button.label = f"🎉 {participants_count}"
        await msg.edit(view=self)

        # Send ephemeral message to the user
        await interaction.followup.send(msg_text, ephemeral=True)

    @discord.ui.button(label="👥 Participants", style=discord.ButtonStyle.secondary)
    async def participants(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        participants_ids = await self.db.get_participants(self.giveaway.id)
        if not participants_ids:
            await interaction.response.send_message(
                f"⚠️ No participants have joined the giveaway **{self.giveaway.title}** yet.",
                ephemeral=True,
            )
            return

        members = [
            f"{idx}. <@{uid}>" for idx, uid in enumerate(participants_ids, start=1)
        ]
        embed = discord.Embed(
            title="Giveaway Participants",
            description=f"These are the members that have participated in the giveaway of **{self.giveaway.title}**:\n"
            + "\n".join(members),
            color=discord.Color.blurple(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
