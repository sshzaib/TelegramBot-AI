from openai import OpenAI
import datetime
from config import OPENAI_API_KEY
from database import get_db, Conversation
from moviepy.editor import VideoFileClip

MODEL = "gpt-4o" #OpenAI model
client = OpenAI(api_key=OPENAI_API_KEY)

#generate AI response 
def generate_ai_response(text, user, imageURL=""):
    #if the user has only provided the image without the caption then send this message and ask the user to ask some question about the image
    if text is None:
        response = "It seems you've uploaded an image file. How can I assist you with this image? If you have any specific questions or need any particular operations performed on it, please let me know!"
        return response
    db = next(get_db())
    #user conversation history from the database based on user
    conversations = db.query(Conversation).filter(Conversation.user == user)
    #format conversations result from database to pass it to AI model
    messages = format_conversations(conversations)
    #if there is no image url provided to the function, add only text else add image url and text 
    if imageURL == "":
        messages.append({"role": "user", "content": text})
    else:
        messages.append(
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": text or ""},
                    {"type": "image_url", "image_url": {"url": imageURL}},
                ],
            }
        )
    #provide all the messages to the AI model to answer considering the history
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.7,
    )
    return response.choices[0].message.content


def generate_ai_response_for_video(base64Frames, user, text):
    db = next(get_db())
    conversations = db.query(Conversation).filter(Conversation.user == user)
    #format the conversation return from the database to pass to the AI model
    messages = format_conversations(conversations)
    #add images & text to the prompt
    messages.append(
        {
            "role": "user",
            "content": [
                f"These are the pictures of an video at frames. Can you answer this question: {text}.",
                *map(lambda x: {"image": x, "resize": 768}, base64Frames[0::60]),
            ],
        }
    )
    params = {"model": MODEL, "messages": messages, "max_tokens": 200}
    result = client.chat.completions.create(**params)
    return result.choices[0].message.content

def format_conversations(conversations):
    messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Try your best to answer the questions. If you can not answer any question just tell the user that you can not answer this question",
                }
            ]
    #add all the user questions and the responses in messages list 
    for conversation in conversations:
        if conversation.imageurl == "":
                user_history = {"role": "user", "content": conversation.text}
        else:
            user_history = {
                "role": "user",
                "content": [
                    {"type": "text", "text": conversation.text or ""},
                    {"type": "image_url", "image_url": {"url": conversation.imageurl}},
                ],
            }
        messages.append(user_history)
        response_history = {"role": "assistant", "content": conversation.response}
        messages.append(response_history)
    print(messages)
    return messages

def generate_text_from_voice_message(audio_path):
    with open(audio_path, "rb") as audio_file:    
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1",
            prompt="",
        )
    return transcription.text

#given the path and the text it converts it into an audio file
def generate_audio_from_text(text, voice_path):
    response = client.audio.speech.create(model="tts-1", voice="alloy", input=text)
    response.stream_to_file(voice_path)

#extract audio from video file
def extract_audio_from_video(video_name):
    video = VideoFileClip(f"data/{video_name}")
    audio = video.audio
    date = datetime.datetime.now()
    audio_name = f"{date.strftime('%f')}.mp3"
    audio_path = f"data/{audio_name}"
    audio.write_audiofile(audio_path)
    audio.close()
    video.close()
    return audio_path
