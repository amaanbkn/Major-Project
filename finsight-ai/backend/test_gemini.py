import asyncio
from services.gemini import classify_intent, get_chat_model

async def main():
    print("Testing gemini...")
    model = get_chat_model()
    try:
        from google.generativeai.types.generation_types import GenerationConfig
        res = await asyncio.wait_for(classify_intent("Hello!"), timeout=10)
        print("RESULT:", res)
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    asyncio.run(main())
