import argparse
import dotenv
import os
import asyncio
from openai import OpenAI
import json
from datetime import datetime


dotenv_file = ".env"
if os.path.isfile(dotenv_file):
    dotenv.load_dotenv(dotenv_file)
API_KEY = os.environ.get("OPENAI_API_KEY")


def ai_translate_eng_word_to_jap(word,context):
    if not API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")
    
    client = OpenAI(api_key=API_KEY)

    # --- PROMPT FOR AI ---
    prompt = f"""
        You are a professional English to Japanese translator for a language-learning app.

        Translate the English word "{word}" into Japanese.
        Context: "{context}" (If empty, translate the most common meaning.)

        Return ONLY valid JSON in the exact format below.

        JSON format:
        {{
        "word": "{word}",
        "translation": "",
        "reading": "",
        "script": "kanji|katakana|hiragana",
        "usage": [
            {{
            "en": "",
            "ja": ""
            }}
        ]
        }}

        Rules:
        - Provide 1–3 usage examples
        - Usage examples must be short and natural
        - Do NOT include romaji
        - Do NOT include any text outside JSON
    """

    # --- API CALL ---
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # You can use "gpt-4o" or "gpt-4-turbo" for larger outputs
        messages=[
            {"role": "system", "content": "You are a language translator of English to Japanese."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=500  # increase if you want more output (may need pagination)
    )

    # --- EXTRACT TEXT OUTPUT ---
    reply_data = response.choices[0].message.content.strip()
    print("RAW:", reply_data)
    print("REPR:", repr(reply_data))

    try:
        reply_dict = json.loads(reply_data)
    except json.JSONDecodeError as e:
        # Handle malformed JSON
        print("JSON parse error:", e)
        reply_dict = None
    return reply_dict



async def main():
    parser = argparse.ArgumentParser(description="Translate an English word to Japanese using OpenAI")
    parser.add_argument("--word", required=True, help="English word to translate")
    parser.add_argument("--context", default="", help="Optional context for the word")

    args = parser.parse_args()

    word = args.word
    context = args.context

    ai_translation_response = ai_translate_eng_word_to_jap(word, context)

    # Ensure output directory exists
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    # Create filename: word_YYYYMMDD_HHMMSS.json
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_word = word.replace(" ", "_").lower()
    filename = f"{safe_word}_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)

    # Save JSON
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(ai_translation_response, f, ensure_ascii=False, indent=2)

    print(f"✅ Translation saved to {filepath}")


if __name__ == "__main__":
    asyncio.run(main())