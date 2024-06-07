from openai import OpenAI
from config import OPENAI_API_KEY
from database import get_db, Conversation

MODEL = "gpt-4o"
client = OpenAI(api_key=OPENAI_API_KEY)


def generate_ai_response(text, user, imageURL=""):
    if text is None:
        response = "It seems you've uploaded an image file. How can I assist you with this image? If you have any specific questions or need any particular operations performed on it, please let me know!"
        return response
    db = next(get_db())
    conversations = db.query(Conversation).filter(Conversation.user == user)  # type: ignore
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant. Try your best to answer the questions. If you can not answer any question just tell the user that you can not answer this question",
        }
    ]
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
    print(messages)
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.7,
    )
    return response.choices[0].message.content


def generate_ai_response_for_video(base64Frames):
    PROMPT_MESSAGES = [
        {
            "role": "user",
            "content": [
                "These are the frames from a video",
                *map(lambda x: {"image": x, "resize": 768}, base64Frames[0::60]),
            ],
        }
    ]
    params = {"model": MODEL, "messages": PROMPT_MESSAGES, "max_tokens": 200}
    result = client.chat.completions.create(**params)
    return result.choices[0].message.content


def generate_text_from_voice_message(voice_path):
    # todo: implement the with open syntax
    transcription = client.audio.transcriptions.create(
        file=open(f"{voice_path}", "rb"),
        model="whisper-1",
        prompt="",
    )
    return transcription.text


def generate_audio_from_text(text, voice_path):
    response = client.audio.speech.create(model="tts-1", voice="alloy", input=text)
    response.stream_to_file(voice_path)
