import asyncio
import json
import argparse
import requests
import os
import dotenv
import uuid
from pathlib import Path

dotenv_file = ".env"
if os.path.isfile(dotenv_file):
    dotenv.load_dotenv(dotenv_file)
ELEVEN_LABS_API_KEY = os.environ.get("ELEVEN_LABS_KEY")

class ElevenLabsAPIError(Exception):
    def __init__(self, status_code: int, detail: dict):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"ElevenLabs API error {status_code}: {detail}")


async def get_audio_from_eleven_labs(jap_text, output_path, voice_id):

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    payload = {
        "text": jap_text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.7
        }
    }
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "insomnia/12.3.0",
        "xi-api-key": ELEVEN_LABS_API_KEY
    }

    response = requests.request("POST", url, json=payload, headers=headers)

    if response.status_code != 200:
        raise ElevenLabsAPIError(
            status_code=response.status_code,
            detail=response.json().get("detail")
        )

    # Write audio bytes to file
    with open(output_path, "wb") as f:
        f.write(response.content)
    return output_path


async def main(filename: str):
    # get project root (parent of current file)
    BASE_DIR = Path(__file__).resolve().parent.parent

    file_path = BASE_DIR / "output" / filename
    audio_dir = BASE_DIR / "audio"
    audio_dir.mkdir(exist_ok=True)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        payload = json.load(f)


    # derive audio filename from JSON filename
    audio_filename = str(uuid.uuid4()) + ".mp3"
    audio_path = audio_dir / audio_filename

    # do something with payload
    print(payload["translation"], audio_path)
    saved_file_location = await get_audio_from_eleven_labs(payload["translation"],audio_path,"EXAVITQu4vr4xnSDxMaL")
    print("OUT: ",saved_file_location)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a JSON output file")
    parser.add_argument(
        "filename",
        help="Name of the JSON file inside the output directory"
    )

    args = parser.parse_args()

    asyncio.run(main(args.filename))