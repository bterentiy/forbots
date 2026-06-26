from telegram import Message, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram import Update

from database import get_user, set_step, set_completed
from data.onboarding_steps import STEPS

TOTAL = len(STEPS)


def _build_keyboard(step: int, from_assistant: bool = False) -> InlineKeyboardMarkup:
    step_data = STEPS[step]
    buttons = []

    if step_data["next_label"] is not None:
        buttons.append([InlineKeyboardButton(
            f"→ Далее: {step_data['next_label']}",
            callback_data=f"step:{step + 1}",
        )])
    else:
        buttons.append([InlineKeyboardButton(
            "🎉 Завершить онбординг",
            callback_data="step:done",
        )])

    buttons.append([InlineKeyboardButton(
        "🤖 Задать вопрос",
        callback_data=f"ask_from:{step}",
    )])

    return InlineKeyboardMarkup(buttons)


def _format_message(step: int) -> str:
    s = STEPS[step]
    header = f"{s['emoji']} <b>{s['title']}</b>\n\n━━━━━━━━━━━━━━━━━━━━\n\n"
    footer = f"\n\n━━━━━━━━━━━━━━━━━━━━\n<i>📍 Шаг {step + 1} из {TOTAL}</i>"
    return header + s["text"] + footer


async def send_step(message: Message, user_id: int, step: int, edit: bool = False):
    text = _format_message(step)
    keyboard = _build_keyboard(step)
    set_step(user_id, step)

    if edit:
        await message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    else:
        await message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)


async def onboarding_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if data.startswith("step:"):
        value = data[len("step:"):]

        if value == "done":
            set_completed(user_id)
            await query.message.edit_text(
                "🎉 <b>Онбординг завершён!</b>\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "Ты прошёл знакомство с INNORTO — отлично!\n\n"
                "Теперь ты знаешь:\n"
                "✅ Историю и миссию компании\n"
                "✅ Ценности и правила команды\n"
                "✅ Условия работы и бонусы\n"
                "✅ К кому обратиться по любому вопросу\n\n"
                "<b>Добро пожаловать в команду! 🚀</b>\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "<i>Напиши любой вопрос — я отвечу</i>",
                parse_mode=ParseMode.HTML,
            )
        else:
            step = int(value)
            await send_step(query.message, user_id, step=step, edit=True)

    elif data.startswith("ask_from:"):
        return_step = int(data[len("ask_from:"):])
        context.user_data["return_to_step"] = return_step
        await query.message.edit_text(
            "🤖 <b>Режим вопроса к ассистенту</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Напиши свой вопрос — я отвечу строго по базе знаний INNORTO.\n\n"
            "━━━━━━━━━━━━━━━━━━━━",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("← Вернуться в онбординг", callback_data=f"step:{return_step}")
            ]]),
        )

    elif data.startswith("back_to_step:"):
        step = int(data[len("back_to_step:"):])
        await send_step(query.message, user_id, step=step, edit=True)
