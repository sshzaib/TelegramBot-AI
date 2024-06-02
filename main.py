import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    filters,
    MessageHandler,
)
from openai import OpenAI
from dotenv import dotenv_values

config = dotenv_values(".env")

MODEL = "gpt-4o"
client = OpenAI(api_key=config["OPENAI_API_KEY"])

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Welcome Ask AI Bot."
    )


async def handleText(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(update)
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant. You have the knowledge of everything. Try you best to answer the questions.",
            },
            {
                "role": "user",
                "content": f"{update.message.text}",
            },
        ],
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=completion.choices[0].message.content
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
    application = ApplicationBuilder().token(config["TOKEN"]).build()

    text_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handleText)
    application.add_handler(text_handler)

    photo_handler = MessageHandler(filters.PHOTO, handlePhoto)
    application.add_handler(photo_handler)

    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(unknown_handler)

    application.run_polling()
