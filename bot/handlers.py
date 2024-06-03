from database.models import User, Conversation
from telegram import Update
from telegram.ext import (
    ContextTypes,
)
from openai_integration import generate_ai_response
from database.manage import get_db


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        db = next(get_db())
        user = User(
            username=update.message.chat.username,  # type: ignore
            firstname=update.message.chat.first_name, # type: ignore
            lastname=update.message.chat.last_name, # type: ignore
        )
        db.add(user)
        db.commit()
    except:
        pass
    finally:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Welcome Ask AI Bot." # type: ignore
        )


MODEL = "gpt-4o"


async def handleText(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text= update.message.text # type: ignore
    db = next(get_db())
    user = db.query(User).filter(User.username == update.message.chat.username).first() # type: ignore
    response = generate_ai_response(text, user) # type: ignore
    if (user):
        conversation = Conversation(
            text=update.message.text, # type: ignore
            imageurl="",
            response=response,
            user=user
        )
        db.add(conversation)
        db.commit()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=response) # type: ignore


async def handlePhoto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await context.bot.get_file(update.message.photo[-1].file_id) # type: ignore
    imageURL = file["file_path"]
    response = generate_ai_response(update.message.caption, imageURL) # type: ignore
    await context.bot.send_message(chat_id=update.effective_chat.id, text=response) # type: ignore


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,  # type: ignore
        text="Sorry, I didn't understand this command.",
    )
