"""Admin commands. Access is restricted via the ADMIN_ID environment variable."""

import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import Config
from database import Database

logger = logging.getLogger(__name__)


def _is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    cfg: Config = context.bot_data["config"]
    return bool(user and cfg.admin_id and user.id == cfg.admin_id)


async def _deny(update: Update) -> None:
    if update.effective_message:
        await update.effective_message.reply_text("🚫 Admin only.")


# ---------------------------------------------------------------------------

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update, context):
        return await _deny(update)
    text = (
        "🛠 *Admin Panel*\n\n"
        "Commands:\n"
        "• /stats – Global statistics\n"
        "• /users – Recent users\n"
        "• /broadcast <text> – Send a message to all users\n"
        "• /addpremium <user_id> – Grant premium\n"
        "• /removepremium <user_id> – Remove premium\n"
        "• /ban <user_id> – Ban user\n"
        "• /unban <user_id> – Unban user\n"
        "• /setlimit <user_id> <limit> – Set custom daily limit"
    )
    await update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update, context):
        return await _deny(update)
    db: Database = context.bot_data["db"]
    s = await db.stats()
    text = (
        "📊 *Bot Statistics*\n\n"
        f"• Total users: {s['total_users']}\n"
        f"• Active today: {s['active_today']}\n"
        f"• Premium users: {s['premium_users']}\n"
        f"• Banned users: {s['banned_users']}\n"
        f"• Total requests: {s['total_requests']}\n"
        f"• Requests today: {s['requests_today']}\n"
        f"• Logged errors: {s['total_errors']}"
    )
    await update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update, context):
        return await _deny(update)
    db: Database = context.bot_data["db"]
    rows = await db.list_users(limit=30)
    if not rows:
        await update.effective_message.reply_text("No users yet.")
        return
    lines = ["👥 *Recent Users*", ""]
    for u in rows:
        flag = "⭐" if u["premium"] else "—"
        banned = " 🚫" if u["banned"] else ""
        uname = f"@{u['username']}" if u["username"] else "—"
        lines.append(f"• `{u['user_id']}` {uname} {flag} req={u['total_requests']}{banned}")
    await update.effective_message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update, context):
        return await _deny(update)
    if not context.args:
        await update.effective_message.reply_text("Usage: /broadcast <message>")
        return
    message = " ".join(context.args)
    db: Database = context.bot_data["db"]
    ids = await db.all_user_ids()
    sent, failed = 0, 0
    for uid in ids:
        try:
            await context.bot.send_message(chat_id=uid, text=message)
            sent += 1
        except Exception:  # noqa: BLE001
            failed += 1
    await update.effective_message.reply_text(f"✅ Sent: {sent}\n❌ Failed: {failed}")


async def addpremium_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update, context):
        return await _deny(update)
    if not context.args or not context.args[0].isdigit():
        await update.effective_message.reply_text("Usage: /addpremium <user_id>")
        return
    db: Database = context.bot_data["db"]
    ok = await db.set_premium(int(context.args[0]), True)
    await update.effective_message.reply_text(
        "✅ Premium enabled." if ok else "⚠️ User not found."
    )


async def removepremium_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update, context):
        return await _deny(update)
    if not context.args or not context.args[0].isdigit():
        await update.effective_message.reply_text("Usage: /removepremium <user_id>")
        return
    db: Database = context.bot_data["db"]
    ok = await db.set_premium(int(context.args[0]), False)
    await update.effective_message.reply_text(
        "✅ Premium removed." if ok else "⚠️ User not found."
    )


async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update, context):
        return await _deny(update)
    if not context.args or not context.args[0].isdigit():
        await update.effective_message.reply_text("Usage: /ban <user_id>")
        return
    db: Database = context.bot_data["db"]
    ok = await db.set_banned(int(context.args[0]), True)
    await update.effective_message.reply_text("✅ User banned." if ok else "⚠️ User not found.")


async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update, context):
        return await _deny(update)
    if not context.args or not context.args[0].isdigit():
        await update.effective_message.reply_text("Usage: /unban <user_id>")
        return
    db: Database = context.bot_data["db"]
    ok = await db.set_banned(int(context.args[0]), False)
    await update.effective_message.reply_text("✅ User unbanned." if ok else "⚠️ User not found.")


async def setlimit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_admin(update, context):
        return await _deny(update)
    if len(context.args) < 2 or not context.args[0].isdigit() or not context.args[1].isdigit():
        await update.effective_message.reply_text("Usage: /setlimit <user_id> <limit>")
        return
    db: Database = context.bot_data["db"]
    ok = await db.set_daily_limit(int(context.args[0]), int(context.args[1]))
    await update.effective_message.reply_text(
        "✅ Limit updated." if ok else "⚠️ User not found."
    )
