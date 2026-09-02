import asyncio
from services.gemini import classify_intent, get_gemini_status


async def main():
    print("Gemini status:", get_gemini_status())
    result = await asyncio.wait_for(classify_intent("Hello!"), timeout=10)
    print("RESULT:", result)


if __name__ == "__main__":
    asyncio.run(main())
