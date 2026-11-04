"""Telegram update handlers: menus, tool flows, account, AI assistant."""

import logging
from typing import Optional

from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import ContextTypes

from ai_service import AIError, AIService
from config import Config
from database import Database
from keyboards import (
    account_keyboard, back_to_category, category_keyboard, category_label,
    chat_active_keyboard, help_keyboard, main_menu_keyboard, tool_active_keyboard,
)
from seo_tools import CATEGORIES, TOOLS
from website_analyzer import (
    UnsafeURLError, analyze_html, fetch_html, format_audit_summary,
)

logger = logging.getLogger(__name__)

WELCOME_TEXT = (
    "👋 *Welcome to High Value Market Bot!*\n\n"
    "Your AI-powered SEO and digital marketing assistant.\n\n"
    "Discover keywords, analyze websites, create SEO content, improve rankings, "
    "research competitors, and develop smarter marketing strategies — all from Telegram.\n\n"
    "Choose a tool below to get started."
)

HELP_TEXT = (
    "❓ *Help & Support*\n\n"
    "How to use the bot:\n"
    "1. Tap any tool from the main menu.\n"
    "2. Follow the on-screen instruction to send your input.\n"
    "3. Receive an AI-generated response in seconds.\n\n"
    "Available commands:\n"
    "• /start – Open the main menu\n"
    "• /help – Show this help message\n"
    "• /about – About this bot\n"
    "• /account – Your account\n"
    "• /endchat – End the AI assistant chat\n\n"
    "Notes:\n"
    "• AI outputs are estimates unless stated otherwise.\n"
    "• Verified SEO metrics require a data provider.\n"
    "• The bot never guarantees rankings, traffic, or sales.\n\n"
    "Need something specific? Use the AI Assistant from the main menu."
)

ABOUT_TEXT = (
    "ℹ️ *About High Value Market Bot*\n\n"
    "An intelligent SEO and digital marketing assistant built for entrepreneurs, "
    "marketers, freelancers, website owners, and agencies.\n\n"
    "What it does:\n"
    "• SEO tooling & analysis\n"
    "• Keyword research & clustering\n"
    "• Public-page website audits\n"
    "• AI content generation\n"
    "• Marketing, social media & backlink strategy\n"
    "• Conversational AI marketing assistant\n\n"
    "Important: this bot uses AI to generate recommendations. "
    "It does not access Google Analytics, Google Search Console, or any private "
    "website data. Verified SEO metrics require a third-party data provider.\n\n"
    "We do not promise guaranteed rankings, traffic, or sales."
)

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _split_message(text: str, limit: int = 4000) -> list[str]:
    if len(text) <= limit:
        return [text]
    chunks, remaining = [], text
    while remaining:
        if len(remaining) <= limit:
            chunks.append(remaining)
            break
        cut = remaining.rfind("\n", 0, limit)
        if cut == -1:
            cut = limit
        chunks.append(remaining[:cut])
        remaining = remaining[cut:].lstrip("\n")
    return chunks


async def _send_long(update: Update, text: str, reply_markup=None) -> None:
    chunks = _split_message(text)
    message = update.effective_message
    if message is None:
        return
    for i, chunk in enumerate(chunks):
        is_last = i == len(chunks) - 1
        await message.reply_text(
            chunk,
            reply_markup=reply_markup if is_last else None,
            disable_web_page_preview=True,
        )


async def _check_and_charge(update: Update, context: ContextTypes.DEFAULT_TYPE, tool: str) -> bool:
    """Return True if user is allowed to use a tool; charge quota only after success elsewhere."""
    db: Database = context.bot_data["db"]
    cfg: Config = context.bot_data["config"]
    user = update.effective_user
    if not user:
        return False

    await db.upsert_user(user.id, user.username, user.first_name)
    record = await db.get_user(user.id)
    if record and record["banned"]:
        await update.effective_message.reply_text(
            "🚫 Your account is restricted. Please contact support."
        )
        return False

    usage = await db.get_usage(user.id)
    limit = usage["override"] if usage["override"] is not None else (
        cfg.premium_daily_limit if usage["premium"] else cfg.free_daily_limit
    )
    if usage["used_today"] >= limit:
        tier = "Premium" if usage["premium"] else "Free"
        await update.effective_message.reply_text(
            f"⏳ You've reached your {tier} daily limit ({limit} requests).\n"
            "Try again tomorrow or contact an admin for a higher limit."
        )
        return False
    return True


async def _charge(update: Update, context: ContextTypes.DEFAULT_TYPE, tool: str, success: bool, error: Optional[str] = None):
    db: Database = context.bot_data["db"]
    user = update.effective_user
    if user:
        await db.touch_usage(user.id, tool, success, error)


async def _ai(update: Update, context: ContextTypes.DEFAULT_TYPE) -> AIService:
    return context.bot_data["ai"]


# ---------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    db: Database = context.bot_data["db"]
    await db.upsert_user(user.id, user.username, user.first_name)
    context.user_data.clear()
    await update.effective_message.reply_text(
        WELCOME_TEXT, parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_keyboard(),
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        HELP_TEXT, parse_mode=ParseMode.MARKDOWN, reply_markup=help_keyboard(),
    )


async def about_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        ABOUT_TEXT, parse_mode=ParseMode.MARKDOWN, reply_markup=help_keyboard(),
    )


async def account_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _show_account(update, context)


async def endchat_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get("state", {}).get("tool") == "ai_assistant":
        context.user_data.pop("state", None)
        context.user_data.pop("chat_history", None)
        await update.effective_message.reply_text(
            "✅ Chat ended. Tap the button below to return to the menu.",
            reply_markup=main_menu_keyboard(),
        )
    else:
        await update.effective_message.reply_text(
            "No active AI chat.", reply_markup=main_menu_keyboard(),
        )


# ---------------------------------------------------------------------------
# account
# ---------------------------------------------------------------------------

async def _show_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db: Database = context.bot_data["db"]
    cfg: Config = context.bot_data["config"]
    user = update.effective_user
    if not user:
        return
    await db.upsert_user(user.id, user.username, user.first_name)
    record = await db.get_user(user.id) or {}
    usage = await db.get_usage(user.id)

    tier = "⭐ Premium" if usage["premium"] else "🆓 Free"
    limit = usage["override"] if usage["override"] is not None else (
        cfg.premium_daily_limit if usage["premium"] else cfg.free_daily_limit
    )
    text = (
        "👤 *My Account*\n\n"
        f"• User ID: `{user.id}`\n"
        f"• Username: @{user.username}" if user.username else f"• User ID: `{user.id}`\n• Username: —"
    )
    text = (
        "👤 *My Account*\n\n"
        f"• User ID: `{user.id}`\n"
        f"• Username: @{user.username if user.username else '—'}\n"
        f"• Status: {tier}\n"
        f"• Total requests: {record.get('total_requests', 0)}\n"
        f"• Used today: {usage['used_today']} / {limit}\n"
        f"• First seen: {record.get('first_seen', '—')[:10]}\n"
        f"• Last seen: {record.get('last_seen', '—')[:10]}\n\n"
        "Contact an admin to upgrade to Premium."
    )
    await update.effective_message.reply_text(
        text, parse_mode=ParseMode.MARKDOWN, reply_markup=account_keyboard(),
    )


# ---------------------------------------------------------------------------
# callback router
# ---------------------------------------------------------------------------

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    await query.answer()
    data = query.data or ""

    if data == "back_main":
        context.user_data.pop("state", None)
        await query.edit_message_text(
            WELCOME_TEXT, parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu_keyboard(),
        )
        return

    if data == "end_chat":
        context.user_data.pop("state", None)
        context.user_data.pop("chat_history", None)
        await query.edit_message_text(
            "✅ Chat ended.", reply_markup=main_menu_keyboard(),
        )
        return

    if data == "menu_account":
        await _show_account_from_query(update, context, query)
        return

    if data == "menu_help":
        await query.edit_message_text(
            HELP_TEXT, parse_mode=ParseMode.MARKDOWN, reply_markup=help_keyboard(),
        )
        return

    if data.startswith("menu_"):
        category = data[len("menu_"):]
        if category in CATEGORIES:
            await query.edit_message_text(
                f"{CATEGORIES[category]['label']}\n\nChoose a tool:",
                reply_markup=category_keyboard(category),
            )
            return

    if data.startswith("tool_"):
        tool_id = data[len("tool_"):]
        await _start_tool(update, context, query, tool_id)
        return


async def _show_account_from_query(update: Update, context: ContextTypes.DEFAULT_TYPE, query) -> None:
    db: Database = context.bot_data["db"]
    cfg: Config = context.bot_data["config"]
    user = update.effective_user
    if not user:
        return
    await db.upsert_user(user.id, user.username, user.first_name)
    record = await db.get_user(user.id) or {}
    usage = await db.get_usage(user.id)
    tier = "⭐ Premium" if usage["premium"] else "🆓 Free"
    limit = usage["override"] if usage["override"] is not None else (
        cfg.premium_daily_limit if usage["premium"] else cfg.free_daily_limit
    )
    text = (
        "👤 *My Account*\n\n"
        f"• User ID: `{user.id}`\n"
        f"• Username: @{user.username if user.username else '—'}\n"
        f"• Status: {tier}\n"
        f"• Total requests: {record.get('total_requests', 0)}\n"
        f"• Used today: {usage['used_today']} / {limit}\n"
        f"• First seen: {record.get('first_seen', '—')[:10]}\n"
        f"• Last seen: {record.get('last_seen', '—')[:10]}\n\n"
        "Contact an admin to upgrade to Premium."
    )
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=account_keyboard())


# ---------------------------------------------------------------------------
# tool dispatch
# ---------------------------------------------------------------------------

async def _start_tool(update: Update, context: ContextTypes.DEFAULT_TYPE, query, tool_id: str) -> None:
    if tool_id == "website_analysis":
        context.user_data["state"] = {"tool": "website_analysis"}
        await query.edit_message_text(
            "🌐 *Website Analysis*\n\nSend me a public URL to audit, e.g. `https://example.com`.\n\n"
            "I will only inspect publicly available HTML — never Google Search Console or private data.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=tool_active_keyboard(),
        )
        return

    if tool_id == "competitor_analysis":
        context.user_data["state"] = {"tool": "competitor_analysis"}
        await query.edit_message_text(
            "⚔️ *Competitor Analysis*\n\nSend up to 3 public competitor URLs separated by spaces or new lines.\n"
            "I will fetch each page, analyze on-page SEO, and generate a competitive report.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=tool_active_keyboard(),
        )
        return

    if tool_id == "ai_assistant":
        context.user_data["state"] = {"tool": "ai_assistant"}
        context.user_data.setdefault("chat_history", [])
        await query.edit_message_text(
            "🤖 *AI Marketing Assistant*\n\nAsk me anything about SEO, digital marketing, "
            "content, keywords, advertising, or business growth. Type /endchat to stop.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=chat_active_keyboard(),
        )
        return

    tool = TOOLS.get(tool_id)
    if not tool:
        await query.edit_message_text("Unknown tool.", reply_markup=main_menu_keyboard())
        return

    context.user_data["state"] = {"tool": tool_id}
    await query.edit_message_text(
        f"*{tool['label']}*\n\n{tool['input_hint']}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=tool_active_keyboard(),
    )


# ---------------------------------------------------------------------------
# text handler (routes inputs to the pending tool)
# ---------------------------------------------------------------------------

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None or not message.text:
        return
    state = context.user_data.get("state") or {}
    tool_id = state.get("tool")
    if not tool_id:
        await message.reply_text(
            "Choose a tool from the menu to get started.",
            reply_markup=main_menu_keyboard(),
        )
        return

    if tool_id == "ai_assistant":
        await _handle_assistant(update, context)
        return

    if tool_id == "website_analysis":
        await _handle_website_analysis(update, context)
        return

    if tool_id == "competitor_analysis":
        await _handle_competitor_analysis(update, context)
        return

    await _handle_ai_tool(update, context, tool_id)


# ---------------------------------------------------------------------------
# AI tools
# ---------------------------------------------------------------------------

async def _handle_ai_tool(update: Update, context: ContextTypes.DEFAULT_TYPE, tool_id: str) -> None:
    message = update.effective_message
    tool = TOOLS.get(tool_id)
    if not tool or message is None:
        return

    if not await _check_and_charge(update, context, tool_id):
        return

    ai: AIService = await _ai(update, context)
    await message.chat.send_action(ChatAction.TYPING)
    try:
        response = await ai.ask(tool["system"], message.text, max_tokens=2500)
    except AIError as exc:
        await _charge(update, context, tool_id, False, str(exc))
        await message.reply_text(
            "⚠️ The AI service is temporarily unavailable. Please try again shortly.",
            reply_markup=tool_active_keyboard(),
        )
        return
    except Exception as exc:  # noqa: BLE001
        logger.exception("AI tool error: %s", exc)
        await _charge(update, context, tool_id, False, str(exc))
        await message.reply_text(
            "⚠️ Something went wrong. Please try again.", reply_markup=tool_active_keyboard(),
        )
        return

    await _charge(update, context, tool_id, True)
    context.user_data["state"] = {"tool": tool_id}  # allow repeat
    await _send_long(update, response, reply_markup=tool_active_keyboard())


# ---------------------------------------------------------------------------
# AI Assistant
# ---------------------------------------------------------------------------

ASSISTANT_SYSTEM = (
    "You are High Value Market Bot's AI Marketing Assistant. You help with SEO, "
    "digital marketing, content strategy, keyword research, advertising, social media, "
    "and business growth. Be concise, practical, and structured. When metrics are "
    "uncertain, label them as estimates. Never guarantee rankings, traffic, or sales. "
    "If the user asks for data you cannot verify, explain that a data provider is needed."
)


async def _handle_assistant(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None or not message.text:
        return
    if not await _check_and_charge(update, context, "ai_assistant"):
        return

    history: list[dict] = context.user_data.setdefault("chat_history", [])
    history.append({"role": "user", "content": message.text})
    history[:] = history[-10:]  # trim

    messages = [{"role": "system", "content": ASSISTANT_SYSTEM}] + history
    ai: AIService = await _ai(update, context)
    await message.chat.send_action(ChatAction.TYPING)
    try:
        reply = await ai.complete(messages, max_tokens=1500)
    except AIError:
        await _charge(update, context, "ai_assistant", False, "ai_error")
        await message.reply_text("⚠️ AI service is busy. Try again in a moment.")
        return
    except Exception as exc:  # noqa: BLE001
        logger.exception("Assistant error: %s", exc)
        await _charge(update, context, "ai_assistant", False, "assistant_error")
        await message.reply_text("⚠️ Something went wrong. Please try again.")
        return

    history.append({"role": "assistant", "content": reply})
    history[:] = history[-10:]
    await _charge(update, context, "ai_assistant", True)
    await _send_long(update, reply, reply_markup=chat_active_keyboard())


# ---------------------------------------------------------------------------
# Website analysis
# ---------------------------------------------------------------------------

async def _handle_website_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None or not message.text:
        return
    if not await _check_and_charge(update, context, "website_analysis"):
        return

    url = message.text.strip()
    await message.chat.send_action(ChatAction.TYPING)
    try:
        final_url, html = await fetch_html(url)
    except UnsafeURLError as exc:
        await _charge(update, context, "website_analysis", False, str(exc))
        await message.reply_text(f"🚫 {exc}", reply_markup=tool_active_keyboard())
        return
    except Exception as exc:  # noqa: BLE001
        logger.exception("Fetch error: %s", exc)
        await _charge(update, context, "website_analysis", False, "fetch_error")
        await message.reply_text(
            "⚠️ Could not fetch this page. Make sure the URL is public and accessible.",
            reply_markup=tool_active_keyboard(),
        )
        return

    try:
        data = analyze_html(html, final_url)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Analyze error: %s", exc)
        await _charge(update, context, "website_analysis", False, "analyze_error")
        await message.reply_text("⚠️ Could not analyze this page.", reply_markup=tool_active_keyboard())
        return

    summary = format_audit_summary(data)
    await _send_long(update, summary)

    # AI-generated recommendations based on the fetched data
    ai: AIService = await _ai(update, context)
    ai_prompt = (
        "Below is structured data extracted from a public web page. Generate a concise "
        "SEO audit with: prioritized fixes, quick wins, and recommended next steps. "
        "Do not invent traffic, rankings, or backlinks.\n\n"
        f"Title: {data['title']}\n"
        f"Meta description: {data['meta_description']}\n"
        f"H1 count: {data['h1_count']} | H1s: {data['h1s']}\n"
        f"Word count: {data['word_count']}\n"
        f"Images: {data['images']} (missing alt: {data['images_missing_alt']})\n"
        f"Canonical: {data['canonical']}\n"
        f"Robots: {data['robots_meta']}\n"
        f"Headings sample: {data['headings'][:25]}\n"
        f"Text sample: {data['text_sample'][:1500]}"
    )
    try:
        analysis = await ai.ask(
            "You are an expert SEO auditor. Be specific and action-oriented.",
            ai_prompt, max_tokens=1800,
        )
    except AIError:
        await _charge(update, context, "website_analysis", True)
        await message.reply_text(
            "✅ Page analysis complete. AI recommendations unavailable right now.",
            reply_markup=tool_active_keyboard(),
        )
        return

    await _charge(update, context, "website_analysis", True)
    await _send_long(update, f"🤖 *AI Recommendations*\n\n{analysis}",
                     reply_markup=tool_active_keyboard())


# ---------------------------------------------------------------------------
# Competitor analysis
# ---------------------------------------------------------------------------

async def _handle_competitor_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message is None or not message.text:
        return
    if not await _check_and_charge(update, context, "competitor_analysis"):
        return

    urls = [u for u in message.text.replace(",", " ").split() if u][:3]
    if not urls:
        await message.reply_text("Send at least one public URL.", reply_markup=tool_active_keyboard())
        return

    await message.chat.send_action(ChatAction.TYPING)
    results = []
    for u in urls:
        try:
            final_url, html = await fetch_html(u)
            results.append(analyze_html(html, final_url))
        except UnsafeURLError as exc:
            results.append({"url": u, "error": str(exc)})
        except Exception as exc:  # noqa: BLE001
            logger.warning("Competitor fetch failed for %s: %s", u, exc)
            results.append({"url": u, "error": "fetch failed"})

    successful = [r for r in results if "error" not in r]
    if not successful:
        await _charge(update, context, "competitor_analysis", False, "all_fetch_failed")
        await message.reply_text(
            "⚠️ Could not fetch any of the URLs. Please check the addresses.",
            reply_markup=tool_active_keyboard(),
        )
        return

    compact = []
    for r in successful:
        compact.append({
            "url": r["url"],
            "title": r["title"],
            "meta_description": r["meta_description"],
            "h1_count": r["h1_count"],
            "word_count": r["word_count"],
            "internal_links": r["internal_links"],
            "external_links": r["external_links"],
            "h1s": r["h1s"],
            "headings": r["headings"][:15],
        })

    ai: AIService = await _ai(update, context)
    prompt = (
        "The following pages are public competitor pages. Generate a competitive SEO report:\n"
        "1. Overview of each competitor (on-page observations only).\n"
        "2. Content strengths & weaknesses.\n"
        "3. Keyword and topic opportunities.\n"
        "4. Content gaps you could target.\n"
        "5. Strategic recommendations.\n"
        "Only use the provided public data. Do not invent traffic, rankings, or backlinks.\n\n"
        f"Data:\n{compact}"
    )
    try:
        report = await ai.ask(
            "You are a senior competitive SEO analyst. Distinguish verified public data "
            "from your own suggestions clearly.",
            prompt, max_tokens=2200,
        )
    except AIError:
        await _charge(update, context, "competitor_analysis", False, "ai_error")
        await message.reply_text("⚠️ AI service unavailable. Please try again.",
                                 reply_markup=tool_active_keyboard())
        return

    await _charge(update, context, "competitor_analysis", True)
    await _send_long(update, f"⚔️ *Competitor Analysis*\n\n{report}",
                     reply_markup=tool_active_keyboard())


# ---------------------------------------------------------------------------
# error handler
# ---------------------------------------------------------------------------

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled error: %s", context.error)
    try:
        db: Database = context.bot_data.get("db")
        uid = None
        if isinstance(update, Update) and update.effective_user:
            uid = update.effective_user.id
        if db:
            await db.log_error(uid, str(context.error))
    except Exception:  # noqa: BLE001
        logger.exception("Failed to log error")
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ An unexpected error occurred. Please try again.",
            )
        except Exception:  # noqa: BLE001
            pass


# ---------------------------------------------------------------------------
# registration
# ---------------------------------------------------------------------------

def register_handlers(application) -> None:
    from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, filters
    from admin import (
        admin_cmd, addpremium_cmd, removepremium_cmd, ban_cmd, unban_cmd,
        setlimit_cmd, stats_cmd, users_cmd, broadcast_cmd,
    )

    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("about", about_cmd))
    application.add_handler(CommandHandler("account", account_cmd))
    application.add_handler(CommandHandler("endchat", endchat_cmd))

    # admin
    application.add_handler(CommandHandler("admin", admin_cmd))
    application.add_handler(CommandHandler("stats", stats_cmd))
    application.add_handler(CommandHandler("users", users_cmd))
    application.add_handler(CommandHandler("broadcast", broadcast_cmd))
    application.add_handler(CommandHandler("addpremium", addpremium_cmd))
    application.add_handler(CommandHandler("removepremium", removepremium_cmd))
    application.add_handler(CommandHandler("ban", ban_cmd))
    application.add_handler(CommandHandler("unban", unban_cmd))
    application.add_handler(CommandHandler("setlimit", setlimit_cmd))

    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    application.add_error_handler(error_handler)
