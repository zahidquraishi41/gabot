import asyncio
import os

from dotenv import load_dotenv
import discord
from discord.ext.commands import Bot

from database import AsyncDatabase
from utils import restore_views


intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = Bot(command_prefix="!", intents=intents)
DB_PATH = "giveaways.db"
db = AsyncDatabase(DB_PATH)


async def load_cogs():
    from cogs.create_giveaway import GiveawayCreate
    from cogs.giveaway_tasks import GiveawayTasks
    from cogs.reroll_giveaway import GiveawayReroll
    from cogs.stop_giveaway import GiveawayStop

    await bot.add_cog(GiveawayCreate(bot, db))
    await bot.add_cog(GiveawayTasks(bot, db))
    await bot.add_cog(GiveawayReroll(bot, db))
    await bot.add_cog(GiveawayStop(bot, db))
    print("Loaded cogs.")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    for giveaway in await db.get_giveaways():
        await restore_views(bot, db, giveaway)


@bot.event
async def on_close():
    await db.close()


async def main():
    await db.connect()
    async with bot:
        await load_cogs()
        load_dotenv()
        TOKEN = os.getenv("DISCORD_TOKEN")
        await bot.start(TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user (Ctrl+C). Goodbye!")
