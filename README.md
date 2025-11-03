# 🎉 Discord Giveaway Bot

A fully asynchronous Discord giveaway bot built with discord.py and SQLite. It provides a clean and reliable way to host giveaways with automated scheduling, persistent storage, and intuitive Discord-based interactions.

&nbsp;

## 🚀 Features

- 🧾 **Slash Commands** for all giveaway operations  
- 🎁 **Create, stop, and reroll giveaways** with full customization  
- 🔁 **Recurring giveaways** — automatically restart after they end  
- 💾 **Persistent database** with async SQLite backend  
- 🧩 **Persistent interactive views** that survive bot restarts  
- 🔒 **Role-based restrictions** and optional role pings  
- 📅 **Duration parsing** (e.g., `1d 2h 30m`)  
- ⚙️ **Automatic scheduling and recovery** on startup  

&nbsp;

## ⚙️ Setup & Requirements

* **Python 3.10+** — [Download Python](https://www.python.org/downloads/)
* A **Discord bot token** — [Create one](https://discord.com/developers/applications)
* Install dependencies:

  ```bash
  pip install -r requirements.txt
  ```
* Create a `.env` file in your project root and add:

  ```env
  DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN_HERE
  ```

&nbsp;

## 📂 Project Structure

```
.
├── main.py                 # Entry point — loads bot, DB, and cogs
├── giveaway.py             # Dataclass defining Giveaway structure
├── utils.py                # Core helper functions for posting and ending giveaways
├── database.py             # Async database handler (not shown)
├── cogs/
│   ├── create_giveaway.py  # /giveaway_create command
│   ├── giveaway_tasks.py   # Background scheduling and recurring management
│   ├── giveaway_view.py    # Interactive join & participants UI
│   ├── reroll_giveaway.py  # /giveaway_reroll command
│   └── stop_giveaway.py    # /giveaway_stop command
└── .env                    # Contains your DISCORD_TOKEN
```

&nbsp;

## 🧠 Commands Overview

| Command            | Description                                                                 |
| ------------------ | --------------------------------------------------------------------------- |
| `/giveaway_create` | Create a new giveaway with custom title, prize, winners, duration, and more |
| `/giveaway_stop`   | Stop an ongoing giveaway early (admin or creator only)                      |
| `/giveaway_reroll` | Reroll an ended giveaway to select new winners                              |

&nbsp;

## 🧱 Database Overview

The bot uses an **asynchronous SQLite database**, which handles all persistent data operations, including:

* 📦 **Storing and retrieving giveaways** (title, prize, duration, creator, etc.)
* 👥 **Tracking participants and winners** with add/remove methods
* 🔄 **Updating giveaway states** (active, stopped, recurring)
* 🧩 **Maintaining consistency** across restarts and scheduled tasks

&nbsp;

## 🏁 License

This project is released under the **MIT License** — free to use, modify, and distribute.

&nbsp;

## 💡 Author

**Md Zahid Quraishi**

> Contributions, pull requests, and feedback are always welcome!
