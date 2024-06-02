from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    filters,
    MessageHandler,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Welcome Ask AI Bot."
    )


MODEL = "gpt-4o"


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
    insert_user(
        update.message.chat.first_name,
        update.message.chat.last_name,
        update.message.chat.username,
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=completion.choices[0].message.content
    )
