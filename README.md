# CyberSec Manager Bot — JSON version

## Railway Variables

Set these variables:

- `BOT_TOKEN` = your BotFather token
- `FOUNDER_ID` = your Telegram numeric ID
- Optional: `DATA_FILE` = `members.json`
- Optional: `RULES_TEXT` = your custom rules

## Important: how the data works

All member data and private notes are stored in `members.json`.

The bot writes the file after every change. It also uses a temporary file + replace operation to reduce the chance of a partially-written JSON file.

### Backup

Open the bot in a private chat and send:

`/backup`

The bot will send you the current `members.json` file. Download it to your phone and keep it somewhere safe.

### Restore on another Railway project/account

1. Stop the old bot.
2. Use `/backup` and save `members.json`.
3. Put that exact `members.json` into the new project next to `bot.py`.
4. Set the same `BOT_TOKEN` and the new project's `FOUNDER_ID`.
5. Start the bot.

The bot will read the old members and notes from that file and continue from there.

## IMPORTANT ABOUT RAILWAY

A normal project filesystem is NOT guaranteed to survive every redeploy/rebuild or replacement of the service.

This JSON version is designed for easy manual backup/restore. If you need automatic persistence through every Railway redeploy/replacement, use a Railway Volume or a database.

Do NOT put `BOT_TOKEN` inside the code or `members.json`.

## Telegram group setup

For reliable join/leave tracking, add the bot to the group and give it the administrator permissions needed to receive member updates.

## Founder-only commands

`/bazza`
`/backup`
`/note ID TEXT`
`/notes ID`
`/delnote ID`
`/find ID`
`/online`
`/stats`

Private member data is intentionally only shown through founder-only commands, and `/bazza` and `/backup` are restricted to the founder's private chat.
