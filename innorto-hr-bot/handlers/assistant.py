import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database import get_user
from core.knowledge import build_context, SYSTEM_PROMPT
from core import llm

log = logging.getLogger(__name__)

THINKING_TEXT = "🔍 Ищу ответ в базе знаний…"
NO_CONTEXT_MSG = (
    "😔 <b>Не нашёл ответ в базе знаний</b>\n\n"
    "━━━━━━━━━━━━━━━━━━━━\n\n"
    "По твоему вопросу нет данных в корпоративной базе знаний.\n\n"
    "Попробуй обратиться напрямую:\n"
    "👤 <b>Кадочникова Екатерина</b> — менеджер по заботе\n"
    "📞 +7 932 128-51-22\n"
    "✉️ zabotainnorto@gmail.com\n\n"
    "━━━━━━━━━━━━━━━━━━━━"
)


async def assistant_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)

    if user is None or user["mode"] not in ("employee", "onboarding"):
        await update.message.reply_text(
            "👋 Напиши /start чтобы начать.",
            parse_mode=ParseMode.HTML,
        )
        return

    query_text = update.message.text.strip()
    thinking_msg = await update.message.reply_text(THINKING_TEXT)

    ctx = build_context(query_text)

    if not ctx:
        return_step = context.user_data.get("return_to_step")
        keyboard = None
        if return_step is not None and user["mode"] == "onboarding":
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("← Вернуться в онбординг", callback_data=f"step:{return_step}")
            ]])
        await thinking_msg.edit_text(NO_CONTEXT_MSG, parse_mode=ParseMode.HTML, reply_markup=keyboard)
        return

    full_prompt = f"{SYSTEM_PROMPT}\n\nБаза знаний:\n{ctx}"

    try:
        answer = llm.ask(full_prompt, query_text)
    except Exception as e:
        log.error("LLM error: %s", e)
        await thinking_msg.edit_text(
            "⚠️ Произошла ошибка при обращении к ассистенту. Попробуй чуть позже.",
            parse_mode=ParseMode.HTML,
        )
        return

    # Добавляем кнопку возврата в онбординг если пользователь пришёл оттуда
    return_step = context.user_data.get("return_to_step")
    if return_step is not None and user["mode"] == "onboarding":
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("← Вернуться в онбординг", callback_data=f"step:{return_step}")
        ]])
        await thinking_msg.edit_text(answer, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    else:
        await thinking_msg.edit_text(answer, parse_mode=ParseMode.HTML)

