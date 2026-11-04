"""Inline keyboard builders."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from seo_tools import CATEGORIES, CATEGORY_TO_TOOLS, TOOLS


def _two_per_row(items: list[tuple[str, str]]) -> list[list[InlineKeyboardButton]]:
    rows: list[list[InlineKeyboardButton]] = []
    for i in range(0, len(items), 2):
        rows.append([InlineKeyboardButton(label, callback_data=data)
                     for label, data in items[i:i + 2]])
    return rows


def main_menu_keyboard() -> InlineKeyboardMarkup:
    rows = _two_per_row([
        ("🔍 SEO Tools", "menu_seo"),
        ("🔑 Keyword Research", "menu_keyword"),
        ("🌐 Website Analysis", "tool_website_analysis"),
        ("⚔️ Competitor Analysis", "tool_competitor_analysis"),
        ("✍️ AI Content Writer", "menu_content"),
        ("📣 Marketing Tools", "menu_marketing"),
        ("📱 Social Media Tools", "menu_social"),
        ("🔗 Backlink Tools", "menu_backlink"),
        ("💼 Business Tools", "menu_business"),
        ("🤖 AI Assistant", "tool_ai_assistant"),
        ("👤 My Account", "menu_account"),
        ("❓ Help & Support", "menu_help"),
    ])
    return InlineKeyboardMarkup(rows)


def category_keyboard(category: str) -> InlineKeyboardMarkup:
    items = [(TOOLS[tid]["label"], f"tool_{tid}") for tid in CATEGORY_TO_TOOLS.get(category, [])]
    rows = _two_per_row(items)
    rows.append([InlineKeyboardButton("⬅️ Main Menu", callback_data="back_main")])
    return InlineKeyboardMarkup(rows)


def tool_active_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel", callback_data="back_main")],
    ])


def chat_active_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛑 End Chat", callback_data="end_chat")],
    ])


def account_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Main Menu", callback_data="back_main")],
    ])


def help_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Main Menu", callback_data="back_main")],
    ])


def back_to_category(category: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back", callback_data=f"menu_{category}"),
         InlineKeyboardButton("🏠 Main Menu", callback_data="back_main")],
    ])


def category_label(category: str) -> str:
    return CATEGORIES.get(category, {}).get("label", "Menu")
