from config.settings import OPENAI_API_KEY, PINECONE_API_KEY
from database.models import User, Conversation
from telegram.ext import (
    ContextTypes,
)
import os
import time
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
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import (
    ConfigurableField,
    RunnablePassthrough,
)
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        db = next(get_db())
        user = User(
            username=update.message.chat.username,  #username of the user
            firstname=update.message.chat.first_name,  #firstname of the user
            lastname=update.message.chat.last_name,  #lastname of the user
        )
        db.add(user)   #add user into the database
        db.commit()
        message = """
        Hello, How can I help you.
        You can:
            🗣️ Send me a voice message and I'll respond by voice
            🤳 Send me a video message and I'll respond by voice
            💬 Send me a chat message and I'll respond by text
            📸 Send me a photo of your day and we can discuss it

        Write /reset at any moment to delete your entire conversation history from our server
        """
        await context.bot.send_message(                     
            chat_id=update.effective_chat.id,
            text=message,   #send this messge to user
        )
    except Exception as e:
        print(e)
    finally:
        next(get_db())


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        db = next(get_db())
        user = db.query(User).filter(User.username == update.message.chat.username).first() #find user in the database
        conversations_to_delete = db.query(Conversation).filter(Conversation.user_id == user.id).all() #get all the conversations of specific user 
        if conversations_to_delete:
            for conversation in conversations_to_delete:
                db.delete(conversation)
            db.commit() #remove all the conversations of the user from the database
            print("conversations deleted successfully.")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Conversation reset",   #send this message to user
            )
        else:
            print("no conversations to delete.")
    except Exception as e:
        print(f"error deleting conversations: {e}")
        await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Error reseting conversation. Enter /start command to register your username in the database",   #send this message to user
            )
    finally:
        next(get_db())


async def handleText(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text #text from the user
        db = next(get_db())
        user = db.query(User).filter(User.username == update.message.chat.username).first() #get user by username
        response = generate_ai_response(text, user) #generate AI response to user message
        if user and response:
            conversation = Conversation(
                text=text, imageurl="", response=response, user=user
            )
            db.add(conversation)    #store reponse to the text in the database
            print(conversation)
            db.commit()
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response)
    except Exception as e:
        print(f"error generating text: {e}")
    finally:
        next(get_db())

async def handlePhoto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.caption #caption of the image
        db = next(get_db())
        user = db.query(User).filter(User.username == update.message.chat.username).first() #user that send the message
        image_file = await context.bot.get_file(update.message.photo[-1].file_id)  #get the image file
        imageURL = image_file["file_path"] #get image url
        response = generate_ai_response(text, user, imageURL)  #generate AI response with the image and the caption 
        if user and response:
            conversation = Conversation(
                text=text, imageurl=imageURL, response=response, user=user
            )
            db.add(conversation)
            db.commit()
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response)
    except Exception as e:
        print(f"error generating response: {e}")
    finally:
        next(get_db())


async def handleAudio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        db = next(get_db())
        user = db.query(User).filter(User.username == update.message.chat.username).first() #get user
        audio_file = await context.bot.get_file(update.message.voice.file_id) #get audio file
        audioUrl = audio_file["file_path"] #audio url
        date = datetime.datetime.now()
        audio_name = f"{date.strftime('%f')}.oga" 
        audio_path = f"data/{audio_name}" #audio path
        urllib.request.urlretrieve(audioUrl, audio_path) 
        text = generate_text_from_voice_message(audio_path) #convert audio message to text
        response = generate_ai_response(text, user) #generate AI response based on the text 
        date = datetime.datetime.now()
        response_audio_path = f"data/{date.strftime('%f')}.oga"
        generate_audio_from_text(response, response_audio_path) #generate audio from text response and save a audio file at that location
        if user and response:
            conversation = Conversation(
                text=text, imageurl="", response=response, user=user
            )
            db.add(conversation) #save the conversation in the database 
            db.commit()
        with open(response_audio_path, "rb") as audio_file:     #send the audio file as response
            await context.bot.send_voice(chat_id=update.effective_chat.id, voice=audio_file)
    except Exception as e:
        print(f"error generating response: {e}")
    finally:
        next(get_db())
        for path in [audio_path, response_audio_path]:
            os.remove(path)
        
async def handleVideo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try: 
        db = next(get_db())
        user = db.query(User).filter(User.username == update.message.chat.username).first()
        video_info = update.message.video #video information
        video_name = "{}-{}x{}.mp4".format(update.update_id, video_info.width, video_info.height) #name of the video file
        video_file = await context.bot.getFile(video_info.file_id) 
        request = requests.get(video_file.file_path, stream=True)
        video_path = f"data/{video_name}"
        with open(video_path, "wb") as video:
            for chunk in request.iter_content(chunk_size=1024):
                if chunk:
                    video.write(chunk)
        downloaded_video = cv2.VideoCapture(video_path)
        base64Frames = []
        #encode images into base64 string array
        while downloaded_video.isOpened():
            success, frame = downloaded_video.read()
            if not success:
                break
            _, buffer = cv2.imencode(".jpg", frame)
            base64Frames.append(base64.b64encode(buffer).decode("utf-8"))
        downloaded_video.release()
        audio_path = extract_audio_from_video(video_name) #extract audio from the video
        text = generate_text_from_voice_message(audio_path) #generate text from the audio
        response = generate_ai_response_for_video(base64Frames, user, text)
        date = datetime.datetime.now()
        response_audio_name = f"{date.strftime('%f')}.oga"
        response_audio_path = f"data/{response_audio_name}"
        generate_audio_from_text(response, response_audio_path) #generate an audio file from the text
        if user and response:
            conversation = Conversation(
                text=text, imageurl="", response=response, user=user
            )
            db.add(conversation)
            db.commit()
        with open(response_audio_path, "rb") as audio_file:  #send the audio file as a response message
            await context.bot.send_voice(chat_id=update.effective_chat.id, voice=audio_file)
    except Exception as e:
        print(f"error generating response: {e}")
    finally:
        next(get_db())
        for path in [audio_path, video_path, response_audio_path]:
            os.remove(path)


async def handleFile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        document = update.message.document
        file = await context.bot.get_file(file_id=document)
        file_path = f"data/{document.file_name}"
        await file.download_to_drive(file_path) #download the file at this location
        loader = PyPDFLoader(file_path) #load this file at this location
        pages = loader.load()
        all_page_contents = "".join([page.page_content for page in pages]) #join all the file content
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=20,
        )
        #split the text into chunks to embed them
        texts = text_splitter.create_documents([all_page_contents])
        embedding_text_list = [text.page_content for text in texts]
        pinecone = Pinecone(api_key=PINECONE_API_KEY)
        index_name = "telegram-bot-index"  # change if desired
        existing_indexes = [index_info["name"] for index_info in pinecone.list_indexes()]
        #if index name does not exist, create a new index
        if index_name not in existing_indexes:
            pinecone.create_index(
                name=index_name,
                dimension=1536,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
            while not pinecone.describe_index(index_name).status["ready"]:
                time.sleep(1)

        index = pinecone.Index(index_name)
        #use OpenAI model to embed the text
        embedding_model = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
        vectorstore = PineconeVectorStore(
            index_name = index_name,
            embedding = embedding_model,
            pinecone_api_key = PINECONE_API_KEY,
        )

        vectorstore.add_texts(embedding_text_list, namespace=update.message.chat.username) #namespace is by username so that any other user can not access the embedded data of anyother user
        template = """You are an helpful assistent. Answer the question based only on the following context.
        {context}
        Question: {question}
        """
        prompt = ChatPromptTemplate.from_template(template)

        model = ChatOpenAI(openai_api_key=OPENAI_API_KEY)
        #vector store is used as a retriver
        retriever = vectorstore.as_retriever()
        # configurable_retriever = retriever.configurable_fields(
        #     search_kwargs=ConfigurableField(
        #         id="search_kwargs",
        #         name="Search Kwargs",
        #         description="The search kwargs to use",
        #     )
        # )
        chain = (
            {"context": retriever, "question": RunnablePassthrough()} #context will be retrived from the vector store & question will be provided afterwords
            | prompt
            | model
            | StrOutputParser()
        )
        response = chain.invoke(
            update.message.caption, #this is the question that is entered in the prompt
            config={ #configure the retriver to only retrive the data of this user based on the username
                "configurable": {
                    "search_kwargs": {"namespace": update.message.chat.username}
                }
            },
        )
        await context.bot.send_message(chat_id=update.effective_chat.id, text=response)
    except Exception as e:
          print(f"error generating response: {e}")
    finally:
        # index = pinecone.Index(index_name)
        # index.delete(delete_all=True, namespace=update.message.chat.username)
        os.remove(file_path) #delete the file that is downloaded in the data directory
        

#in case of an unknown command send the message
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand this command.",
    )
