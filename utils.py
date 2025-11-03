import random

import discord
from discord.ext.commands import Bot

from database import AsyncDatabase
from giveaway import Giveaway
from cogs.giveaway_view import GiveawayView


def parse_duration(text: str) -> int:
    """
    Parse duration string like '1d 2h 3m 4s' into total seconds.
    Acceptable units: d, h, m, s
    Must have spaces between different units.
    """
    units = {"d": 86400, "h": 3600, "m": 60, "s": 1}
    total = 0

    parts = text.strip().split()
    for part in parts:
        if len(part) < 2 or not part[:-1].isdigit() or part[-1] not in units:
            raise ValueError("❌ Invalid duration format. Use like '1d 2h 3m 4s'.")
        total += int(part[:-1]) * units[part[-1]]

    return total


async def post_giveaway(bot: Bot, db: AsyncDatabase, giveaway: Giveaway):
    giveaway.id = await db.add_giveaway(giveaway)

    embed = discord.Embed(title=giveaway.title, color=discord.Color.blurple())
    embed.description = (
        f"Click 🎉 button to enter!\n"
        f"ID: {giveaway.id}\n"
        f"Prize: {giveaway.prize}\n"
        f"Winners: {giveaway.winners_count}\n"
        f"Ends <t:{giveaway.ends_at}:R>\n\n"
    )
    if giveaway.host_id:
        embed.description += f"Hosted by: <@{giveaway.host_id}>\n"
    if giveaway.criteria:
        embed.description += f"Criteria: {giveaway.criteria}\n"
    if giveaway.required_role_id:
        embed.description += f"Must have the role: <@&{giveaway.required_role_id}>\n"
    if giveaway.recurring:
        embed.set_footer(text="This giveaway will recur automatically.")

    view = await GiveawayView.create(db, giveaway)
    guild = bot.get_guild(giveaway.guild_id)
    channel = guild.get_channel(giveaway.channel_id)
    msg = await channel.send(embed=embed, view=view)
    giveaway.message_id = msg.id
    await db.set_message_id(msg.id, giveaway.id)

    if giveaway.required_role_id and giveaway.ping_role:
        role = guild.get_role(giveaway.required_role_id)
        if role:
            if role.mentionable or channel.permissions_for(guild.me).mention_everyone:
                await channel.send(
                    f"{role.mention} 🎉 **{giveaway.title}** has started!"
                )
            else:
                print(f"⚠️ Bot can't ping role: {giveaway.required_role_id}")
        else:
            print("⚠️ Role not found")


async def end_giveaway(bot: Bot, db: AsyncDatabase, giveaway: Giveaway, channel):
    """
    Disables a specific button in a message, keeping other buttons intact,
    and updates the embed to show that the giveaway ended.
    """
    try:
        msg = await channel.fetch_message(giveaway.message_id)
    except discord.NotFound:
        print(f"⚠️ Message {giveaway.message_id} was deleted.")
        return
    except discord.HTTPException:
        print("⚠️ Failed to fetch message due to an API error.")
        return

    # Update embed description
    if msg.embeds:
        embed = msg.embeds[0]
        desc_lines = embed.description.splitlines()
        for i, line in enumerate(desc_lines):
            if line.startswith("Ends "):
                desc_lines[i] = "Ended"
        embed.description = "\n".join(desc_lines)
    else:
        embed = None

    # Disable join button
    view = await GiveawayView.create(db, giveaway)
    for child in view.children:
        if child.label.startswith("🎉"):
            child.disabled = True

    bot.add_view(view, message_id=giveaway.message_id)
    await msg.edit(view=view, embed=embed)
    print(f"✅ Giveaway {giveaway.id} ended and buttons disabled.")


async def announce_winner(db: AsyncDatabase, giveaway: Giveaway, channel):
    participants = await db.get_participants(giveaway.id)
    print(f"Participants for Giveaway {giveaway.id} are ", participants)
    if participants:
        sysrand = random.SystemRandom()
        winners = sysrand.sample(
            participants, k=min(giveaway.winners_count, len(participants))
        )
        print(f"Winners for Giveaway {giveaway.id} are ", winners)
        await db.add_winners(giveaway.id, winners)
        winners_mentions = " ".join(f"<@{uid}>" for uid in winners)
        result_text = (
            f"🎉 Congratulations {winners_mentions}! You won **{giveaway.prize}**!\n"
            f"📩 Direct Message the host to claim your prize!"
        )
    else:
        result_text = f"⚠️ No participants joined the giveaway **{giveaway.title}**. No winners this time."

    await channel.send(result_text)


async def restore_views(bot: Bot, db: AsyncDatabase, giveaway: Giveaway):
    channel = bot.get_channel(giveaway.channel_id)
    if channel is None:
        print(f"⚠️ Channel {giveaway.channel_id} not found. Skipping restore.")
        return

    try:
        await channel.fetch_message(giveaway.message_id)
    except discord.NotFound:
        print(f"⚠️ Message {giveaway.message_id} was deleted. Skipping restore.")
        return

    # Re-add view since message still exists
    view = await GiveawayView.create(db, giveaway)
    bot.add_view(view, message_id=giveaway.message_id)
    print(f"✅ View restored for giveaway {giveaway.id}.")
