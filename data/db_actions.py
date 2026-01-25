from typing import List
from pydantic import BaseModel
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from .models import Translation, TranslationUsage, TranslationAudio
from .db import engine
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker, selectinload
from pathlib import Path
from datetime import datetime
import json

class Usage(BaseModel):
    en: str
    ja: str

    class Config:
        orm_mode = True  # important for SQLAlchemy ORM objects
        from_attributes=True


class TranslationResponse(BaseModel):
    word: str
    translation: str
    reading: str | None
    script: str
    usages: List[Usage] = []

    class Config:
        orm_mode = True
        from_attributes=True

class TranslationAudioResponse(BaseModel):
    id: int
    translation_id: int
    storage_url: str
    voice_id: str | None
    audio_format: str
    created_at: datetime

    class Config:
        from_attributes = True  # SQLAlchemy compatibility

# async def insert_translation(session: AsyncSession, payload: dict) -> TranslationResponse:
#     """
#     Inserts a translation with its usages into the database.
#     Returns a Pydantic model for response.
#     """
#     # Check if the word + translation + reading already exists
#     stmt = select(Translation).where(
#         Translation.word == payload["word"],
#         Translation.translation == payload["translation"],
#         Translation.reading == payload.get("reading")
#     )
#     result = await session.execute(stmt)
#     existing = result.scalars().first()

#     if existing:
#         # Optional: you could merge new usages if needed
#         return TranslationResponse.from_orm(existing)

#     # Create translation row
#     translation = Translation(
#         word=payload["word"],
#         translation=payload["translation"],
#         reading=payload.get("reading"),
#         script=payload["script"],
#         usages=[
#             TranslationUsage(en=u["en"], ja=u["ja"]) for u in payload.get("usage", [])
#         ]
#     )

#     session.add(translation)

#     try:
#         await session.commit()
#         await session.refresh(translation)
#     except IntegrityError:
#         await session.rollback()
#         raise

#     # Return Pydantic response
#     return TranslationResponse.from_orm(translation)


# async def insert_translation(session: AsyncSession, payload: dict) -> TranslationResponse:
#     stmt = select(Translation).options(
#         selectinload(Translation.usages)
#     ).where(
#         Translation.word == payload["word"],
#         Translation.translation == payload["translation"],
#         Translation.reading == payload.get("reading")
#     )

#     result = await session.execute(stmt)
#     existing = result.scalars().first()

#     if existing:
#         # usages are already eagerly loaded
#         return TranslationResponse.from_orm(existing)

#     # Create translation row
#     translation = Translation(
#         word=payload["word"],
#         translation=payload["translation"],
#         reading=payload.get("reading"),
#         script=payload["script"],
#         usages=[
#             TranslationUsage(en=u["en"], ja=u["ja"]) for u in payload.get("usage", [])
#         ]
#     )

#     session.add(translation)

#     try:
#         await session.commit()
#         await session.refresh(translation)
#     except IntegrityError:
#         await session.rollback()
#         raise

#     return TranslationResponse.from_orm(translation)


async def insert_translation(session: AsyncSession, payload: dict) -> TranslationResponse:
    # Check if exists
    stmt = select(Translation).options(selectinload(Translation.usages)).where(
        Translation.word == payload["word"],
        Translation.translation == payload["translation"],
        Translation.reading == payload.get("reading")
    )
    result = await session.execute(stmt)
    existing = result.scalars().first()
    if existing:
        return TranslationResponse.model_validate(existing)

    # Create new translation
    translation = Translation(
        word=payload["word"],
        translation=payload["translation"],
        reading=payload.get("reading"),
        script=payload["script"],
        usages=[TranslationUsage(en=u["en"], ja=u["ja"]) for u in payload.get("usage", [])]
    )

    session.add(translation)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise

    # Reload with usages eagerly loaded
    stmt = select(Translation).options(selectinload(Translation.usages)).where(
        Translation.id == translation.id
    )
    result = await session.execute(stmt)
    translation_with_usages = result.scalars().first()

    return TranslationResponse.model_validate(translation_with_usages)


async def insert_translation_audio(
    db: AsyncSession,
    translation_id: int,
    storage_url: str,
    voice_id: str | None = None,
    audio_format: str = "mp3",
) -> TranslationAudioResponse:
    audio = TranslationAudio(
        translation_id=translation_id,
        storage_url=storage_url,
        voice_id=voice_id,
        audio_format=audio_format,
    )

    db.add(audio)
    await db.commit()
    await db.refresh(audio)

    return TranslationAudioResponse.model_validate(audio)


async def main():
    # 1️⃣ Read JSON file
    # get project root (parent of current file)
    # BASE_DIR = Path(__file__).resolve().parent.parent

    # filename = BASE_DIR / "output" / "fart_20260123_084755.json"

    # with open(filename, "r", encoding="utf-8") as f:
    #     payload = json.load(f)

    # # 2️⃣ Create async session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # 3️⃣ Insert translation
        #response = await insert_translation(session, payload)

        response = await insert_translation_audio(session,1,"https://japanese-translations.nl-ams-1.linodeobjects.com/japanese-translate/0ead6ffb-80f0-4351-8104-97ed96c46fd0.mp3","EXAVITQu4vr4xnSDxMaL")

        # 4️⃣ Print the Pydantic response as JSON
        print(response.json())


if __name__ == "__main__":
    asyncio.run(main())