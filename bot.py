import json
import os
from datetime import datetime, timezone

from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    ChatMemberHandler,
    ContextTypes,
)

BOT_TOKEN = os.environ["BOT_TOKEN"]
FOUNDER_ID = int(os.environ["FOUNDER_ID"])

# Railway Volume-ի դեպքում սա կարող է լինել /data/members.json
DATA_FILE = os.environ.get("DATA_FILE", "members.json")

DEFAULT_RULES = """🛡️ Խմբի կանոններ

1. Հարգանքով շփվեք բոլոր անդամների հետ։
2. Մի հրապարակեք ուրիշների անձնական տվյալները։
3. Չի թույլատրվում վնասաբեր ծրագրերի կամ վտանգավոր հղումների տարածում։
4. Կիբեռանվտանգության փորձարկումները կատարեք միայն թույլտվությամբ և լաբորատոր միջավայրում։
5. Սպամը, խարդախությունը և խաբեությունը արգելվում են։
6. Խախտումների դեպքում դիմեք հիմնադրին։
7. Պահպանեք Telegram-ի և խմբի կանոնները։
"""

RULES_TEXT = os.environ.get("RULES_TEXT", DEFAULT_RULES)


def now():
    return datetime.now(timezone.utc).isoformat()


def load_members():
    folder = os.path.dirname(DATA_FILE)
    if folder:
        os.makedirs(folder, exist_ok=True)

    if not os.path.exists(DATA_FILE):
        save_members({})

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_members(data):
    folder = os.path.dirname(DATA_FILE)
    if folder:
        os.makedirs(folder, exist_ok=True)

    temp = DATA_FILE + ".tmp"
    with open(temp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    os.replace(temp, DATA_FILE)


def upsert_member(user, status="member"):
    members = load_members()
    uid = str(user.id)

    old = members.get(uid, {})
    members[uid] = {
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "joined_at": old.get("joined_at", now()),
        "last_seen_at": now(),
        "status": status,
        "notes": old.get("notes", []),
    }

    save_members(members)


def is_founder(update):
    return update.effective_user and update.effective_user.id == FOUNDER_ID


def format_member(m):
    username = f"@{m['username']}" if m.get("username") else "չկա"
    name = " ".join(
        x for x in [m.get("first_name"), m.get("last_name")] if x
    ) or "չկա"

    notes = m.get("notes", [])
    notes_text = "\n".join(f"  • {n}" for n in notes) if notes else "  • չկա"

    return (
        f"ID: {m.get('user_id')}\n"
        f"Անուն: {name}\n"
        f"Username: {username}\n"
        f"Status: {m.get('status', 'unknown')}\n"
        f"Joined: {m.get('joined_at', 'unknown')}\n"
        f"Last seen: {m.get('last_seen_at', 'unknown')}\n"
        f"Notes:\n{notes_text}"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user:
        upsert_member(user, "member")

    await update.message.reply_text(
        f"🛡️ Բարի գալուստ, {user.first_name}!\n\n"
        f"Քո Telegram ID-ն՝ `{user.id}`\n\n"
        f"Կարդա /rules և օգտագործիր /help։",
        parse_mode="Markdown",
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 Հրամաններ\n\n"
        "/start — բացել բոտը\n"
        "/help — հրամանների ցանկ\n"
        "/rules — խմբի կանոններ\n"
        "/id — քո Telegram ID-ն\n\n"
        "👑 Հիմնադրի հրամաններ\n"
        "/bazza — անդամների բազա\n"
        "/backup — members.json-ի backup\n"
        "/note ID TEXT — անձնական նշում\n"
        "/notes ID — ցույց տալ նշումները\n"
        "/delnote ID — ջնջել նշումները\n"
        "/find ID — գտնել անդամին\n"
        "/online — ներկա անդամներ\n"
        "/stats — վիճակագրություն"
    )


async def rules_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(RULES_TEXT)


async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 Քո Telegram ID-ն՝ `{update.effective_user.id}`",
                                    parse_mode="Markdown")


async def bazza_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_founder(update):
        await update.message.reply_text("⛔ Այս հրամանը հասանելի է միայն հիմնադրին։")
        return

    if update.effective_chat.type != "private":
        await update.message.reply_text("🔒 /bazza-ն օգտագործիր բոտի private chat-ում։")
        return

    members = load_members()
    if not members:
        await update.message.reply_text("Բազան դեռ դատարկ է։")
        return

    items = []
    for m in members.values():
        items.append(format_member(m))

    text = "👑 Մասնակիցների բազա\n\n" + "\n\n────────────\n\n".join(items)

    # Telegram message limit
    for i in range(0, len(text), 3800):
        await update.message.reply_text(text[i:i+3800])


async def backup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_founder(update):
        await update.message.reply_text("⛔ Այս հրամանը հասանելի է միայն հիմնադրին։")
        return

    if update.effective_chat.type != "private":
        await update.message.reply_text("🔒 /backup-ն օգտագործիր բոտի private chat-ում։")
        return

    if not os.path.exists(DATA_FILE):
        save_members({})

    with open(DATA_FILE, "rb") as f:
        await update.message.reply_document(
            document=f,
            filename="members.json",
            caption="📦 Բազայի backup\nՊահիր այս ֆայլը անվտանգ տեղում։"
        )


async def note_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_founder(update):
        await update.message.reply_text("⛔ Այս հրամանը հասանելի է միայն հիմնադրին։")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Օրինակ՝ /note 123456789 Լավ մասնակից է")
        return

    uid = context.args[0]
    note = " ".join(context.args[1:])

    members = load_members()
    if uid not in members:
        await update.message.reply_text("❌ Այդ ID-ն բազայում չկա։")
        return

    members[uid].setdefault("notes", []).append(note)
    save_members(members)

    await update.message.reply_text("✅ Նշումը պահպանվեց։")


async def notes_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_founder(update):
        await update.message.reply_text("⛔ Այս հրամանը հասանելի է միայն հիմնադրին։")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Օրինակ՝ /notes 123456789")
        return

    uid = context.args[0]
    members = load_members()

    if uid not in members:
        await update.message.reply_text("❌ Այդ ID-ն բազայում չկա։")
        return

    notes = members[uid].get("notes", [])
    if not notes:
        await update.message.reply_text("📝 Նշումներ չկան։")
        return

    await update.message.reply_text(
        "📝 Նշումներ\n\n" + "\n".join(f"{i+1}. {n}" for i, n in enumerate(notes))
    )


async def delnote_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_founder(update):
        await update.message.reply_text("⛔ Այս հրամանը հասանելի է միայն հիմնադրին։")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Օրինակ՝ /delnote 123456789")
        return

    uid = context.args[0]
    members = load_members()

    if uid not in members:
        await update.message.reply_text("❌ Այդ ID-ն բազայում չկա։")
        return

    members[uid]["notes"] = []
    save_members(members)
    await update.message.reply_text("🗑️ Նշումները ջնջվեցին։")


async def find_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_founder(update):
        await update.message.reply_text("⛔ Այս հրամանը հասանելի է միայն հիմնադրին։")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Օրինակ՝ /find 123456789")
        return

    uid = context.args[0]
    members = load_members()

    if uid not in members:
        await update.message.reply_text("❌ Չգտնվեց։")
        return

    await update.message.reply_text(format_member(members[uid]))


async def online_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_founder(update):
        await update.message.reply_text("⛔ Այս հրամանը հասանելի է միայն հիմնադրին։")
        return

    members = load_members()
    current = [m for m in members.values() if m.get("status") == "member"]

    if not current:
        await update.message.reply_text("👥 Ներկա անդամներ չկան բազայում։")
        return

    lines = []
    for m in current:
        username = f"@{m['username']}" if m.get("username") else m.get("first_name", "Unknown")
        lines.append(f"• {username} — `{m['user_id']}`")

    await update.message.reply_text(
        f"🟢 Ներկա անդամներ՝ {len(current)}\n\n" + "\n".join(lines),
        parse_mode="Markdown",
    )


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_founder(update):
        await update.message.reply_text("⛔ Այս հրամանը հասանելի է միայն հիմնադրին։")
        return

    members = load_members()
    total = len(members)
    active = sum(1 for m in members.values() if m.get("status") == "member")
    left = sum(1 for m in members.values() if m.get("status") == "left")

    await update.message.reply_text(
        "📊 Բազայի վիճակագրություն\n\n"
        f"Ընդհանուր գրանցված՝ {total}\n"
        f"Ներկա՝ {active}\n"
        f"Դուրս եկած՝ {left}"
    )


async def member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cm = update.chat_member
    if not cm:
        return

    user = cm.new_chat_member.user
    if user.is_bot:
        return

    new_status = cm.new_chat_member.status
    old_status = cm.old_chat_member.status

    if new_status in ("member", "administrator", "creator"):
        was_left = old_status in ("left", "kicked")
        upsert_member(user, "member")

        if was_left:
            username = f"@{user.username}" if user.username else "չկա"
            await context.bot.send_message(
                chat_id=cm.chat.id,
                text=(
                    f"👋 Բարի վերադարձ, {user.first_name}!\n\n"
                    f"🆔 ID: {user.id}\n"
                    f"👤 Username: {username}\n"
                    f"📜 Կարդա /rules"
                ),
            )

    elif new_status in ("left", "kicked"):
        upsert_member(user, "left")


async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("start", "Բացել բոտը"),
        BotCommand("help", "Հրամանների ցանկ"),
        BotCommand("rules", "Չատի կանոններ"),
        BotCommand("id", "Իմ Telegram ID-ն"),
        BotCommand("bazza", "Հիմնադրի բազա"),
        BotCommand("backup", "Բազայի backup"),
        BotCommand("note", "Անձնական նշում"),
        BotCommand("notes", "Ցույց տալ նշումը"),
        BotCommand("delnote", "Ջնջել նշումները"),
        BotCommand("find", "Գտնել ID-ով"),
        BotCommand("online", "Ներկա անդամներ"),
        BotCommand("stats", "Բազայի վիճակ"),
    ])


def main():
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("rules", rules_cmd))
    app.add_handler(CommandHandler("id", id_cmd))
    app.add_handler(CommandHandler("bazza", bazza_cmd))
    app.add_handler(CommandHandler("backup", backup_cmd))
    app.add_handler(CommandHandler("note", note_cmd))
    app.add_handler(CommandHandler("notes", notes_cmd))
    app.add_handler(CommandHandler("delnote", delnote_cmd))
    app.add_handler(CommandHandler("find", find_cmd))
    app.add_handler(CommandHandler("online", online_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))

    app.add_handler(ChatMemberHandler(
        member_update,
        ChatMemberHandler.CHAT_MEMBER
    ))

    print(f"Bot started. Data file: {DATA_FILE}")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
