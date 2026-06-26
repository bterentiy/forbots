from dotenv import load_dotenv
load_dotenv()

import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

from telegram import BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from database import init_db
from handlers.start import start_handler, mode_callback
from handlers.onboarding import onboarding_callback
from handlers.assistant import assistant_handler


async def post_init(app):
    await app.bot.set_my_commands([
        BotCommand("start", "Перезапустить / сменить режим"),
    ])
    init_db()


def main():
    token = os.environ["BOT_TOKEN"]
    app = (
        Application.builder()
        .token(token)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start_handler))

    # Inline кнопки — выбор режима при /start
    app.add_handler(CallbackQueryHandler(mode_callback, pattern=r"^mode:"))

    # Inline кнопки — шаги онбординга и вопрос к ассистенту
    app.add_handler(CallbackQueryHandler(onboarding_callback, pattern=r"^(step:|ask_from:|back_to_step:)"))

    # Свободный текст → ассистент
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, assistant_handler))

    print("🤖 INNORTO HR Bot запущен...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
