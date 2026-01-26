#from typing import Union, List
from fastapi import FastAPI, Depends, HTTPException, Header, Query, status
from pydantic import BaseModel, HttpUrl
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import Optional, List
#from data.actions import get_or_add_user
import os, requests, dotenv, base64, json
from uvicorn import Config, Server
from data.db import engine
from data.s3_storage import upload_to_s3
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from data.db_actions import (
    TranslationResponse,
    TranslationAudioResponse,
    insert_translation,
    insert_translation_audio,
    get_translation_with_audio_by_word,   
)
from authentication.auth import get_api_key
from ai.generate_audio import get_audio_from_eleven_labs, ElevenLabsAPIError
from ai.translate_eng_jap import ai_translate_eng_word_to_jap
import uuid
from pathlib import Path
#import bleach


app = FastAPI()
#basedir = os.path.abspath(os.path.dirname(__file__))



origins=['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# del os.environ["GL_CLIENT_REDIRECT_URI"]
# del os.environ["FB_CLIENT_REDIRECT_URI"]
# del os.environ["X_REDIRECT_URI"]

# #LOAD ENVIRONMENT
dotenv_file = ".env"
if os.path.isfile(dotenv_file):
    dotenv.load_dotenv(dotenv_file)


# CLIENT_ID = os.environ.get("CLIENT_ID")
# CLIENT_SECRET = os.environ.get("CLIENT_SECRET")

# REDIRECT_URI="https://welcome-capital-jaybird.ngrok-free.app"

#RESPONSE MODELS

class TranslationWithAudioResponse(BaseModel):
    translation: TranslationResponse
    audio: TranslationAudioResponse


#INPUT MODELS

class InputWord(BaseModel):
    word : str
    context : str
    voice_id : Optional[str] = None




@app.post('/translatewordengtojap', response_model=TranslationWithAudioResponse)
async def translate_word_eng_jap(input_word : InputWord, api_key: str = Depends(get_api_key)):
    #TODO:
    #Sanatize the input ? If necessary 
    #Check the DB first if the word already exists
    #Setup db session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        translation, audio = await get_translation_with_audio_by_word(session,input_word.word)
        if translation and audio:
            return TranslationWithAudioResponse(
                translation,
                audio
            )
        
    print("INPUT WORD: ", input_word)

    #Generate the translation
    # # 2️⃣ Create async session

    translation = ai_translate_eng_word_to_jap(input_word.word, input_word.context)
    print("Translation", translation["translation"])

    #Insert into the databse
    async with async_session() as session:
        inserted_translation = await insert_translation(session,translation)

    print("INSERTED TRANSLATION", inserted_translation)

    #Generate the audio file
    BASE_DIR = Path(__file__).resolve().parent
    audio_dir = BASE_DIR / "audio"
    audio_dir.mkdir(exist_ok=True)
    audio_filename = str(uuid.uuid4()) + ".mp3"
    audio_path = audio_dir / audio_filename


    voice_id = input_word.voice_id if input_word.voice_id else "EXAVITQu4vr4xnSDxMaL"

    try:
        audio_file_path = await get_audio_from_eleven_labs(translation['translation'],audio_path,voice_id)
    except ElevenLabsAPIError as elae:
        print("ELAE", elae)
        if elae.status_code == 404:
            raise HTTPException(status_code=404, detail=f"A voice with the voice id ${voice_id} was not found.")
        else:
            raise HTTPException(status_code=400, detail="An error occurred generating the audio.")
    except Exception as e:
        raise HTTPException(status_code=400, detail="An error occurred generating the audio.")

    print("GENERATED AUDIO ", audio_file_path)

    #Upload the audio file to S3 storage
    with open(audio_file_path, "rb") as f:
        #Get the file data required for transferring to S3
        audio_data = f.read()
    storage_url = await upload_to_s3(audio_data,audio_filename)
    print("UPLOADED FILE ", storage_url)


    #Update the database
    async with async_session() as session:
        inserted_audio_file = await insert_translation_audio(session,inserted_translation.id,storage_url,voice_id,"mp3")
    print("INSERTED AUDIO ", inserted_audio_file)
    response = TranslationWithAudioResponse(
        translation=inserted_translation,
        audio=inserted_audio_file
    )

    return response






async def start_fastapi():
    config = Config(app=app, host="0.0.0.0", port=8000, loop="asyncio", reload=True)
    server = Server(config)
    await server.serve()

async def start_all():
    await asyncio.gather(
        start_fastapi()
    )

if __name__ == "__main__":
    asyncio.run(start_all())