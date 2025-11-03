import asyncio
from dataclasses import replace

from discord.ext import commands, tasks
from discord.utils import utcnow

from database import AsyncDatabase
from giveaway import Giveaway
from utils import end_giveaway, post_giveaway, announce_winner


class GiveawayTasks(commands.Cog):
    def __init__(self, bot: commands.Bot, db: AsyncDatabase):
        self.bot = bot
        self.db = db
        self.active_tasks = {}
        self.failsafe_loop.start()
        bot.loop.create_task(self.schedule_existing_giveaways())

    def cog_unload(self):
        """Cancel all running tasks on cog unload."""
        for task in self.active_tasks.values():
            task.cancel()
        self.failsafe_loop.cancel()

    async def schedule_existing_giveaways(self):
        """Schedule all active giveaways when the bot starts."""
        await self.bot.wait_until_ready()
        now = int(utcnow().timestamp())
        active_giveaways = await self.db.get_giveaways(active=1)
        for giveaway in active_giveaways:
            remaining = giveaway.ends_at - now
            if remaining <= 0:
                # Already overdue, handle in failsafe loop
                continue
            self.schedule_giveaway_task(giveaway, remaining)

    def schedule_giveaway_task(self, giveaway: Giveaway, delay: float):
        """Schedule a giveaway to end after a certain delay (seconds)."""
        if giveaway.id in self.active_tasks:
            self.active_tasks[giveaway.id].cancel()

        task = self.bot.loop.create_task(self._giveaway_task(giveaway, delay))
        self.active_tasks[giveaway.id] = task

    async def _giveaway_task(self, giveaway: Giveaway, delay: float):
        """Waits for the delay and ends the giveaway."""
        try:
            await asyncio.sleep(delay)
            await self.end_giveaway_process(giveaway)
        except asyncio.CancelledError:
            return
        finally:
            self.active_tasks.pop(giveaway.id, None)

    async def end_giveaway_process(self, giveaway: Giveaway):
        """Ends a giveaway and announces winners."""
        g = await self.db.get_giveaway(giveaway.id)
        if not g or not g.active:
            print("⚠️ Giveaway was deleted or stopped")
            return

        await self.db.set_inactive(giveaway.id)
        channel = self.bot.get_channel(giveaway.channel_id)
        if not channel:
            print(
                f"⚠️ Channel {giveaway.channel_id} not found for giveaway {giveaway.id}."
            )
            return

        await end_giveaway(self.bot, self.db, giveaway, channel)
        await announce_winner(self.db, giveaway, channel)

        # Handle recurring giveaways
        if giveaway.recurring:
            created_at = int(utcnow().timestamp())
            ends_at = created_at + giveaway.ends_at - giveaway.created_at
            new_giveaway = replace(
                giveaway,
                id=None,
                message_id=None,
                created_at=created_at,
                ends_at=ends_at,
                active=1,
            )
            await post_giveaway(self.bot, self.db, new_giveaway)
            self.schedule_giveaway_task(
                new_giveaway, ends_at - int(utcnow().timestamp())
            )

    @tasks.loop(minutes=1)
    async def failsafe_loop(self):
        """Periodic sweep to catch any giveaways that were missed (bot restart, crashes, etc.)."""
        now = int(utcnow().timestamp())
        active_giveaways = await self.db.get_giveaways(active=1)
        for giveaway in active_giveaways:
            remaining = giveaway.ends_at - now
            if remaining <= 0:
                if giveaway.id not in self.active_tasks:
                    await self.end_giveaway_process(giveaway)
            else:
                if giveaway.id not in self.active_tasks:
                    self.schedule_giveaway_task(giveaway, remaining)

    @failsafe_loop.before_loop
    async def before_failsafe(self):
        await self.bot.wait_until_ready()
