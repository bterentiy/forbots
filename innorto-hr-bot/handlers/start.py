from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database import get_user, set_mode

WELCOME_TEXT = (
    "👋 <b>Привет! Я HR-помощник INNORTO</b>\n\n"
    "━━━━━━━━━━━━━━━━━━━━\n\n"
    "Я помогу тебе:\n"
    "• Познакомиться с компанией в первый день\n"
    "• Найти нужного коллегу по любому вопросу\n"
    "• Разобраться в правилах и регламентах\n\n"
    "<b>Выбери, что тебе подходит:</b>"
)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🆕 Первый день", callback_data="mode:onboarding")],
        [InlineKeyboardButton("👤 Я уже работаю", callback_data="mode:employee")],
    ])
    await update.message.reply_text(
        WELCOME_TEXT,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )


async def mode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id

    if data == "mode:onboarding":
        set_mode(user_id, "onboarding")
        from handlers.onboarding import send_step
        await send_step(query.message, user_id, step=0, edit=True)

    elif data == "mode:employee":
        set_mode(user_id, "employee")
        await query.message.edit_text(
            "👤 <b>Режим помощника активирован</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Напиши свой вопрос в свободной форме:\n"
            "<i>Например: «где взять новую продукцию?» или «кто занимается договорами?»</i>\n\n"
            "━━━━━━━━━━━━━━━━━━━━",
            parse_mode=ParseMode.HTML,
        )
