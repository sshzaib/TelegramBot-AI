import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    filters,
    MessageHandler,
)
from openai import OpenAI
import sqlalchemy as db
from config import OPENAI_API_KEY, BOT_TOKEN

engine = db.create_engine("sqlite:///db.sqlite3", echo=True)
connection = engine.connect()

metadata = db.MetaData()

user_table = db.Table(
    "user",
    metadata,
    db.Column("id", db.Integer, primary_key=True),
    db.Column("username", db.String),
    db.Column("firstname", db.String),
    db.Column("lastname", db.String),
)
MODEL = "gpt-4o"
client = OpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


async def handlePhoto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await context.bot.get_file(update.message.photo[-1].file_id)
    fileURL = file["file_path"]
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant. Help me with this",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"{update.message.caption}",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": fileURL},
                    },
                ],
            },
        ],
        temperature=0.0,
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=response.choices[0].message.content
    )


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand this command.",
    )


if __name__ == "__main__":
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    metadata.create_all(engine)

    text_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handleText)
    application.add_handler(text_handler)

    photo_handler = MessageHandler(filters.PHOTO, handlePhoto)
    application.add_handler(photo_handler)

    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(unknown_handler)

    application.run_polling()
