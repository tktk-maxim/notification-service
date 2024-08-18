import logging
from typing import Optional

from fastapi import HTTPException
from telegram import Update
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

import threading
import time
import asyncio

from utils import (get_telegram_name, get_user_by_telegram_name, linking_chat_id_to_user, send_message,
                   checking_tasks_for_time_expiration_and_sending_msg)
from config import settings


def schedule_function():
    while True:
        asyncio.run(checking_tasks_for_time_expiration_and_sending_msg())
        time.sleep(60)


scheduler_thread = threading.Thread(target=schedule_function)
scheduler_thread.daemon = True
scheduler_thread.start()


bot = Bot(token=settings.telegram_token)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Send me any message and I will tell you your chat ID.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id

    telegram_name = await get_telegram_name(chat_id, bot)
    try:
        user = await get_user_by_telegram_name(telegram_name)
    except HTTPException:
        await update.message.reply_text("Your telegram account is not authorized in the employee accounting system")
        raise HTTPException(status_code=404, detail="Employee obj not found")

    message = f"Account: @{user.telegram_name} is already registered"
    if user.chat_id == 0:
        message = await linking_chat_id_to_user(chat_id, user=user.__dict__)
    await send_message(user.chat_id, message)


def main() -> None:
    application = ApplicationBuilder().token(settings.telegram_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()


if __name__ == '__main__':
    main()
