import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    filters,
    MessageHandler,
)
from openai import OpenAI
import os
from dotenv import dotenv_values

config = dotenv_values(".env")

MODEL = "gpt-4o"
client = OpenAI(api_key=config["OPENAI_API_KEY"])

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ai = "this is openai response"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=ai)


async def ai_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant. Help me with my math homework!",
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


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand this command.",
    )


if __name__ == "__main__":
    application = ApplicationBuilder().token(config["TOKEN"]).build()

    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), ai_handler)
    application.add_handler(echo_handler)

    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(unknown_handler)

    application.run_polling()
