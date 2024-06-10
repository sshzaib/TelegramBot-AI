from config.settings import OPENAI_API_KEY, PINECONE_API_KEY
from database.models import User, Conversation
from telegram.ext import (
    ContextTypes,
)
from telegram import Update
from openai_integration import (
    generate_ai_response,
    generate_text_from_voice_message,
    generate_audio_from_text,
    generate_ai_response_for_video,
)
from database.manage import get_db
import urllib
import datetime
import requests
import cv2
import base64
from openai_integration.api import extract_audio_from_video
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import (
    ConfigurableField,
    RunnableBinding,
    RunnableLambda,
    RunnablePassthrough,
)
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


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
            db.query(User).filter(User.username == update.message.chat.username).first()
        )
        conversations_to_delete = (
            db.query(Conversation).filter(Conversation.user_id == user.id).all()
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
    user = db.query(User).filter(User.username == update.message.chat.username).first()
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
    user = db.query(User).filter(User.username == update.message.chat.username).first()
    # type: ignore
    file = await context.bot.get_file(update.message.photo[-1].file_id)
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
    user = db.query(User).filter(User.username == update.message.chat.username).first()
    file = await context.bot.get_file(update.message.voice.file_id)
    voiceUrl = file["file_path"]
    date = datetime.datetime.now()
    audio_name = f"{date.strftime('%f')}.oga"
    user_voice_path = f"data/{audio_name}"
    urllib.request.urlretrieve(voiceUrl, user_voice_path)
    text = generate_text_from_voice_message(audio_name)
    response = generate_ai_response(text, user)
    date = datetime.datetime.now()
    random_path = {date.strftime("%f")}
    response_voice_path = f"data/{random_path}.oga"
    generate_audio_from_text(response, response_voice_path)
    if user and response:
        conversation = Conversation(
            text=text, imageurl="", response=response, user=user
        )
        db.add(conversation)
        db.commit()
    with open(response_voice_path, "rb") as voice_file:
        await context.bot.send_voice(chat_id=update.effective_chat.id, voice=voice_file)


async def handleVideo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(update)
    video = update.message.video  # a video
    video_name = "{}-{}x{}.mp4".format(update.update_id, video.width, video.height)
    tfile = await context.bot.getFile(video.file_id)
    r = requests.get(tfile.file_path, stream=True)
    with open(f"data/{video_name}", "wb") as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    downloaded_video = cv2.VideoCapture(f"data/{video_name}")
    base64Frames = []
    while downloaded_video.isOpened():
        success, frame = downloaded_video.read()
        if not success:
            break
        _, buffer = cv2.imencode(".jpg", frame)
        base64Frames.append(base64.b64encode(buffer).decode("utf-8"))
    downloaded_video.release()
    audio_name = extract_audio_from_video(video_name)
    text = generate_text_from_voice_message(audio_name)
    db = next(get_db())
    user = db.query(User).filter(User.username == update.message.chat.username).first()
    response = generate_ai_response_for_video(base64Frames, user, text)
    date = datetime.datetime.now()
    response_audio_name = f"{date.strftime('%f')}.oga"
    response_audio_path = f"data/{response_audio_name}"
    generate_audio_from_text(response, response_audio_path)
    if user and response:
        conversation = Conversation(
            text=text, imageurl="", response=response, user=user
        )
        db.add(conversation)
        db.commit()
    with open(response_audio_path, "rb") as audio_file:
        await context.bot.send_voice(chat_id=update.effective_chat.id, voice=audio_file)


async def handleFile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(update)
    document = update.message.document
    file = await context.bot.get_file(file_id=document)
    await file.download_to_drive(f"data/{document.file_name}")
    loader = PyPDFLoader(f"data/{document.file_name}")
    pages = loader.load()
    all_page_contents = "".join([doc.page_content for doc in pages])
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=20,
        length_function=len,
        is_separator_regex=False,
    )
    texts = text_splitter.create_documents([all_page_contents])
    embedding_text_list = [text.page_content for text in texts]
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index_name = "telegram-bot-index"  # change if desired
    existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]
    if index_name not in existing_indexes:
        pc.create_index(
            name=index_name,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        while not pc.describe_index(index_name).status["ready"]:
            time.sleep(1)

    index = pc.Index(index_name)
    embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)

    vectorstore = PineconeVectorStore(
        index_name=index_name,
        embedding=embeddings,
        pinecone_api_key=PINECONE_API_KEY,
    )

    vectorstore.add_texts(embedding_text_list, namespace=update.message.chat.username)
    template = """You are an helpful assistent. Answer the question based only on the following context.
    {context}
    Question: {question}
    """
    prompt = ChatPromptTemplate.from_template(template)

    model = ChatOpenAI(openai_api_key=OPENAI_API_KEY)

    retriever = vectorstore.as_retriever()
    configurable_retriever = retriever.configurable_fields(
        search_kwargs=ConfigurableField(
            id="search_kwargs",
            name="Search Kwargs",
            description="The search kwargs to use",
        )
    )
    chain = (
        {"context": configurable_retriever, "question": RunnablePassthrough()}
        | prompt
        | model
        | StrOutputParser()
    )
    response = chain.invoke(
        update.message.caption,
        config={
            "configurable": {
                "search_kwargs": {"namespace": update.message.chat.username}
            }
        },
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand this command.",
    )
