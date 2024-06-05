import logging
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    filters,
    MessageHandler,
)
import sqlalchemy as db
from config import BOT_TOKEN
from bot import start, handleText, handlePhoto, handleAudio, unknown, reset

engine = db.create_engine("sqlite:///db.sqlite3", echo=True)
connection = engine.connect()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

if __name__ == "__main__":
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    start_handler = CommandHandler("start", start)
    application.add_handler(start_handler)

    reset_handler = CommandHandler("reset", reset)
    application.add_handler(reset_handler)

    text_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handleText)
    application.add_handler(text_handler)

    photo_handler = MessageHandler(filters.PHOTO, handlePhoto)
    application.add_handler(photo_handler)

    audio_handler = MessageHandler(filters.VOICE, handleAudio)
    application.add_handler(audio_handler)

    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(unknown_handler)

    application.run_polling()
