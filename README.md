# Lain-Bot

A Discord leveling bot themed around Serial Experiments Lain, built because every XP bot I found felt the same and I wanted something with a bit more personality.

Instead of "levels" you climb through 13 Layers of the Wired. Chat, react, sit in voice with people, or check in daily and it all counts toward XP. Hit Layer 13 and you can prestige to loop back with a permanent rank.

## Features

* XP from chatting, reacting to messages, sitting in voice channels, and a daily bonus command
* 13 layers total, capped, no infinite grinding
* Prestige system - reset back to Layer 0 for a permanent Prestige rank (I, II, III...)
* Per-user cooldowns so people can't spam messages or reactions to farm XP
* Voice XP only counts if there's at least one other real person in the channel, so you can't just sit alone with your mic off
* Progress persists between restarts, stored locally as JSON
* `=xphelp` breaks down exactly how much XP each action gives and how long the cooldowns are

## Project structure

```
lain-bot/
├── src/
│   ├── main.py          # entry point - loads cogs and starts the bot
│   ├── config.py         # prefix, xp amounts, cooldowns, layer cap
│   ├── data.py             # flavor lines used in level-up messages
│   └── cogs/
│       ├── events.py         # startup, sets bot status
│       └── xp.py               # the whole leveling system
├── data_store/               # xp_data.json, created automatically on first run
└── requirements.txt
```

## Install dependencies

```
pip install -r requirements.txt
```

`requirements.txt`:
```
discord.py>=2.3.0
```

## Setup

You'll need your own bot token from the [Discord Developer Portal](https://discord.com/developers/applications). Create an application, add a bot to it, and copy the token from the Bot tab.

Lain-Bot reads the token from an environment variable instead of hardcoding it in the file:

```
export DISCORD_BOT_TOKEN="add_your_own_bot_token_here"
```

You'll also need to enable **Server Members Intent** and **Message Content Intent** for your bot under the same Bot tab, or the bot won't start.

## Usage

```
python3 src/main.py
```

Once it's running and invited to your server, everything happens automatically in chat. Prefix is `=`.

| Command | What it does |
|---|---|
| `=rank [@user]` | shows your current layer, prestige, and XP progress |
| `=layers` | server leaderboard, sorted by prestige then XP |
| `=daily` | claim a one-time XP bonus, resets every 24h |
| `=prestige` | reset to Layer 0 for a permanent rank, only works at Layer 13 |
| `=xphelp` | explains every way to earn XP and the exact amounts/cooldowns |

## How it works

1. Every message, reaction, and voice session grants a random amount of XP, each with its own cooldown so nothing can be spammed for free progress.
2. 100 XP moves you up one layer. There are 13 layers total, matching the show.
3. XP still accumulates past Layer 13 in the background, but your displayed layer stays capped until you prestige.
4. `=prestige` resets your XP to 0 and adds one to your prestige count, shown as a roman numeral next to your name.
5. All progress is saved to a local JSON file, so restarting the bot doesn't wipe anyone's XP.

## Disclaimer

This is a personal project built for a small Discord server, not something meant to scale. Keep your bot token out of version control - it's read from an environment variable specifically so it never ends up in the code.
