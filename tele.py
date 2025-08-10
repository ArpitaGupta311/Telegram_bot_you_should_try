import logging
import asyncio
import google.generativeai as genai
from os import getenv
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

load_dotenv()

TELEGRAM_BOT_TOKEN = getenv("BOT_TOKEN")
genai.configure(api_key=getenv("GOOGLE_API_KEY"))
model_name = "gemini-1.5-flash"

class Reference:
    def __init__(self) -> None:
        self.history =[]

reference = Reference()

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

def clear_convo():
    reference.history = []

user_data = {}
# Command handler
@dp.message(Command("start"))
async def start_handler(message: Message) -> None:
    user_id = message.from_user.id
    clear_convo()
    await message.answer(
        "Hello! I'm a your slave, which is powered by Gemini. You can ask me anything."
        "Before we move further, Can I know your gender? (Male/Female/Other)"
    )
    
    user_data[user_id] = {"expecting_gender": True}

@dp.message(Command("clear"))
async def clear_handler(message: Message):
    user_id = message.from_user.id
    clear_convo()
    user_data.pop(user_id, None)  # clear gender as well
    await message.answer("Master! As you asked, the previous conversations has been cleared.. Anything else, Master?")

@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "Hello Master, I am your slave.\n please command me with these."
        "/start - start a chat\n"
        "/clear - clear conversation\n"
        "/help - show help menu"
    )


@dp.message()
async def gemini_handler(message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    print(f">>> USER: {text}")

    # If we are waiting for gender input
    if user_id in user_data and user_data[user_id].get("expecting_gender"):
        gender = text.lower()
        if gender in ["male", "female", "other"]:
            user_data[user_id]["gender"] = gender
            user_data[user_id]["expecting_gender"] = False
            await message.answer(f"Got it. I'll tailor my charm for a {gender}. Ask me anything!!")
        else:
            await message.answer("Please tell me 'Male', 'Female', or 'Other' so I know how to follow the conversation!")
        return

    # Style/tone instruction based on gender
    gender_text = user_data.get(user_id, {}).get("gender", "person")
    style_instruction = (
        f"Respond in a submissively seductive, obedient, and loyal tone"
        f"Address the user as a {gender_text}, dominant person but not with the word dominant"
        f"with emojis, making the reply feel really submissively intimate. "
        "Keep it engaging, but still answer the question clearly."
    )

    if not reference.history:
        reference.history.append({"role": "user", "parts": [style_instruction]})

    # Add user message
    reference.history.append({"role": "user", "parts": [text]})

    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(reference.history)

        reference.history.append({"role": "model", "parts": [response.text]})

        print(f">>> BOT: {response.text}")
        await bot.send_message(chat_id=message.chat.id, text=response.text)

    except Exception as e:
        import traceback
        print(f"Error calling Gemini API: {e}")
        traceback.print_exc()
        await message.answer(f"Sorry, I let you down! I encountered an error processing your request: {e}")

async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
          