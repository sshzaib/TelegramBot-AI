from database.models import User, Conversation
from telegram import Update
from telegram.ext import (
    ContextTypes,
)
from openai_integration import generate_ai_response, generate_text_from_voice_message
from database.manage import get_db
import urllib
import random
import datetime
import os


MODEL = "gpt-4o"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        db = next(get_db())
        user = User(
            username=update.message.chat.username,  # type: ignore
            firstname=update.message.chat.first_name,  # type: ignore
            lastname=update.message.chat.last_name,  # type: ignore
        )
        db.add(user)
        db.commit()
    except Exception as e:
        print(e)
    finally:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Welcome Ask AI Bot.",  # type: ignore
        )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        db = next(get_db())
        user = (
            db.query(User).filter(User.username ==
                                  update.message.chat.username).first()
        )
        conversations_to_delete = (
            db.query(Conversation).filter(
                Conversation.user_id == user.id).all()
        )
        if conversations_to_delete:
            for conversation in conversations_to_delete:
                db.delete(conversation)
            db.commit()
            print("conversations deleted successfully.")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Conversation reset",  # type: ignore
            )
        else:
            print("no conversations to delete.")
    except Exception as e:
        print(f"error deleting conversations: {e}")
    finally:
        next(get_db())


async def handleText(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text  # type: ignore
    db = next(get_db())
    user = db.query(User).filter(User.username ==
                                 update.message.chat.username).first()
    response = generate_ai_response(text, user)  # type: ignore
    if user and response:
        conversation = Conversation(
            text=text, imageurl="", response=response, user=user
        )
        db.add(conversation)
        db.commit()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)


async def handlePhoto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.caption
    db = next(get_db())
    user = db.query(User).filter(User.username ==
                                 update.message.chat.username).first()
    # type: ignore
    file = await context.bot.get_file(update.message.photo[-1].file_id)["file_path"]
    imageURL = file["file_path"]
    response = generate_ai_response(text, user, imageURL)  # type: ignore
    if user and response:
        conversation = Conversation(
            text=text, imageurl=imageURL, response=response, user=user
        )
        db.add(conversation)
        db.commit()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)


async def handleAudio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = next(get_db())
    user = db.query(User).filter(User.username ==
                                 update.message.chat.username).first()
    file = await context.bot.get_file(update.message.voice.file_id)
    voiceUrl = file["file_path"]
    date = datetime.datetime.now()
    random_path = {date.strftime("%f")}
    voice_path = f"data/{random_path}.oga"
    urllib.request.urlretrieve(voiceUrl, voice_path)
    text = generate_text_from_voice_message(voice_path)
    print(text)
    response = generate_ai_response(text, user)
    print(response)
    if user and response:
        conversation = Conversation(
            text=text, imageurl="", response=response, user=user
        )
        db.add(conversation)
        db.commit()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand this command.",
    )
