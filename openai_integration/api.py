from openai import OpenAI
from config import OPENAI_API_KEY
from database import get_db, Conversation

MODEL = "gpt-4o"
client = OpenAI(api_key=OPENAI_API_KEY)


def generate_ai_response(text, user, imageURL=""):
    if imageURL:
        return message_with_image(text, imageURL)
    else:
        return message_without_image(text, user)


def message_with_image(text, imageURL):
    db = next(get_db())
    conversations = db.query(Conversation).filter(Conversation.user == user) # type: ignore
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant. Try your best to answer the questions. If you can not answer any question just tell the user that you can not answer this question",
        }
    ]
    for conversation in conversations:
        user_history = {
            "role": "user",
            "content": [
                
            ]
        }
        messages.append(user_history)
        response_history = {
            "role": "assistant",
            "content": conversation.response
        }
        messages.append(response_history)





    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant. Try your best to answer the questions. If you can not answer any question just tell the user that you can not answer this question",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"{text}",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": imageURL},
                    },
                ],
            },
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content


def message_without_image(text, user):
    db = next(get_db())
    conversations = db.query(Conversation).filter(Conversation.user == user) # type: ignore
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant. You have all the information. Try your best to answer the questions. If you can not answer any question just tell the user that you can not answer this question",
        }
    ]
    for conversation in conversations:
        user_history = {
            "role": "user",
            "content": conversation.text
        }
        messages.append(user_history)
        response_history = {
            "role": "assistant",
            "content": conversation.response
        }
        messages.append(response_history)

    messages.append({
        "role": "user",
        "content": text
    })
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages, # type: ignore
        temperature=0.7,
    )

    return response.choices[0].message.content
