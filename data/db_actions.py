from typing import List
from pydantic import BaseModel
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from .models import Translation, TranslationUsage, TranslationAudio, TranslationUsageAudio
from .db import engine
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker, selectinload, joinedload
from pathlib import Path
from datetime import datetime
import json


class UsageAudio(BaseModel):
    id : int
    usage_id : int
    storage_url : str
    voice_id : str
    audio_format : str
    created_at : datetime

    class Config:
        from_attributes=True

class Usage(BaseModel):
    id: int  # DB primary key
    en: str
    ja: str
    usage_audio : UsageAudio | None

    class Config:
        from_attributes=True

class UsageWithoutAudio(BaseModel):
    id: int  # DB primary key
    en: str
    ja: str

    class Config:
        from_attributes=True

# class UsageWithoutAudio(BaseModel):
#     id: int  # DB primary key
#     en: str
#     ja: str
#     usage_audio : UsageAudio | None

#     class Config:
#         from_attributes=True


class TranslationResponse(BaseModel):
    id: int  # DB primary key
    word: str
    translation: str
    reading: str | None
    script: str
    usages: List[Usage] = []

    class Config:
        from_attributes=True

class TranslationResponseWithoutUsageAudio(BaseModel):
    id: int  # DB primary key
    word: str
    translation: str
    reading: str | None
    script: str
    usages: List[UsageWithoutAudio] = []

    class Config:
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

class TranslationWithAudioResponse(BaseModel):
    translation: TranslationResponse
    audio: TranslationAudioResponse | None

class LinkResponse(BaseModel):
    usage_id : int
    id : int
    storage_url : str
    created_at : datetime

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


# async def insert_translation(session: AsyncSession, payload: dict) -> TranslationResponse:
#     # Check if exists
#     stmt = select(Translation).options(selectinload(Translation.usages)).where(
#         Translation.word == payload["word"],
#         Translation.translation == payload["translation"],
#         Translation.reading == payload.get("reading")
#     )
#     result = await session.execute(stmt)
#     existing = result.scalars().first()
#     if existing:
#         return TranslationResponse.model_validate(existing)

#     # Create new translation
#     translation = Translation(
#         word=payload["word"],
#         translation=payload["translation"],
#         reading=payload.get("reading"),
#         script=payload["script"],
#         usages=[TranslationUsage(en=u["en"], ja=u["ja"]) for u in payload.get("usage", [])]
#     )

#     session.add(translation)
#     try:
#         await session.commit()
#     except IntegrityError:
#         await session.rollback()
#         raise

#     # Reload with usages eagerly loaded
#     stmt = select(Translation).options(selectinload(Translation.usages)).where(
#         Translation.id == translation.id
#     )
#     result = await session.execute(stmt)
#     translation_with_usages = result.scalars().first()

#     return TranslationResponse.model_validate(translation_with_usages)

async def insert_translation(session: AsyncSession, payload: dict) -> TranslationResponse:
    # Check if translation exists
    stmt = select(Translation).options(selectinload(Translation.usages)).where(
        Translation.word == payload["word"],
        Translation.translation == payload["translation"],
        Translation.reading == payload.get("reading")
    )

    # stmt = (
    #     select(Translation)
    #     .where(Translation.id == translation.id)
    #     .options(
    #         selectinload(Translation.usages)
    #         .selectinload(TranslationUsage.usage_audio)
    #     )
    # )

    print("PAYLOAD", payload)

    # stmt = (
    #     select(Translation)
    #     .options(
    #         selectinload(Translation.usages)
    #         .selectinload(TranslationUsage.usage_audio)
    #     )
    #     .where(Translation.id == translation.id)
    # )
    result = await session.execute(stmt)
    existing = result.scalars().first()
    if existing:
        return TranslationResponseWithoutUsageAudio.model_validate(existing)
    
    # translation = result.scalars().first()
    # if translation:
    #     return TranslationResponse.model_validate(translation)

    # Create new translation + usages
    #TODO
    #THIS INSERTS, but it is unable to return the response properly
    #On second attempt it works because it is returning a different path
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

    # Reload translation with usages eagerly loaded (for Pydantic)
    stmt = select(Translation).options(selectinload(Translation.usages)).where(
        Translation.id == translation.id
    )

    # stmt = select(Translation).options(selectinload(Translation.usages)).where(
    #     Translation.word == payload["word"],
    #     Translation.translation == payload["translation"],
    #     Translation.reading == payload.get("reading")
    # )
    result = await session.execute(stmt)
    translation_with_usages = result.scalars().first()
    #ATTEMPT BELOW DOES NOT WORK
    # new_usages = []
    # for u in translation_with_usages.usages:
    #     print("USAGE", u.__dict__)
    #     new_usages.append(Usage(
    #         id=u.id,
    #         en=u.en,
    #         ja=u.ja,
    #         usage_audio=None
    #     ))
    # translation_with_usages.usages = new_usages
    # print("DO I GET HERE")
    # translation_response = TranslationResponse(
    #     id=translation_with_usages.id,
    #     word=translation_with_usages.word,
    #     translation=translation_with_usages.translation,
    #     reading= translation_with_usages.reading,
    #     script=translation_with_usages.script,
    #     usages=new_usages
    # )    
    # return translation_response
    #return TranslationResponse.model_validate(translation)
    # ────────────────────────────────────────────────
    # 3. MANUAL construction — avoids any schema confusion
    usages_list = []
    for usage in translation.usages:
        print("THIS IS USAGE", usage.__dict__)
        usages_list.append(
            Usage(
                id=usage.id,
                en=usage.en,
                ja=usage.ja,
                usage_audio=None
            )
        )

    response = TranslationResponse(
        id=translation.id,
        word=translation.word,
        translation=translation.translation,
        reading=translation.reading,
        script=translation.script,
        usages=usages_list,
    )
    return response
    #return TranslationResponseWithoutUsageAudio.model_validate(translation_with_usages)



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


# async def add_usage_audio(
#     session: AsyncSession,
#     translation_id: int,
#     usage_id: int,
#     storage_url: str,
#     voice_id: str | None = None,
#     audio_format: str = "mp3"
# ) -> TranslationUsageAudio:
#     """
#     Insert a new audio file and link it to a usage.

#     Raises ValueError if this usage already has an audio linked.
#     Returns the linking object.
#     """

#     # 1️⃣ Create TranslationAudio row
#     audio = TranslationAudio(
#         translation_id=translation_id,
#         storage_url=storage_url,
#         voice_id=voice_id,
#         audio_format=audio_format,
#     )
#     session.add(audio)
#     await session.flush()  # ensures `audio.id` is populated

#     # 2️⃣ Create the linking row
#     link = TranslationUsageAudio(
#         usage_id=usage_id,
#         audio_id=audio.id
#     )
#     session.add(link)

#     try:
#         await session.commit()
#         await session.refresh(link)
#     except IntegrityError:
#         await session.rollback()
#         raise ValueError(f"Usage ID {usage_id} already has an audio linked.")

#     return link


# async def add_usage_audio(
#     session: AsyncSession,
#     translation_id: int,
#     usage_id: int,
#     storage_url: str,
#     voice_id: str | None = None,
#     audio_format: str = "mp3"
# ) -> TranslationUsageAudio:
#     """
#     Create audio and link it to a usage.
#     If the usage already has audio, return the existing link.
#     """

#     try:
#         # 1️⃣ Create TranslationAudio
#         audio = TranslationAudio(
#             translation_id=translation_id,
#             storage_url=storage_url,
#             voice_id=voice_id,
#             audio_format=audio_format,
#         )
#         session.add(audio)
#         await session.flush()  # get audio.id

#         # 2️⃣ Create linking row
#         link = TranslationUsageAudio(
#             usage_id=usage_id,
#             audio_id=audio.id
#         )
#         session.add(link)

#         await session.commit()

#         # 🔁 Reload link WITH audio eagerly loaded
#         stmt = (
#             select(TranslationUsageAudio)
#             .options(selectinload(TranslationUsageAudio.audio))
#             .where(TranslationUsageAudio.id == link.id)
#         )
#         result = await session.execute(stmt)
#         link = result.scalars().one()

#         return link

#     except IntegrityError:
#         await session.rollback()

#         # 🔁 Fetch existing link WITH audio eagerly loaded
#         stmt = (
#             select(TranslationUsageAudio)
#             .options(selectinload(TranslationUsageAudio.audio))
#             .where(TranslationUsageAudio.usage_id == usage_id)
#         )
#         result = await session.execute(stmt)
#         existing = result.scalars().first()

#         if existing:
#             return existing
        
#         raise RuntimeError("Integrity error but no existing usage-audio link found")


async def add_usage_audio(
    session: AsyncSession,
    usage_id: int,
    storage_url: str,
    voice_id: str | None = None,
    audio_format: str = "mp3",
) -> TranslationUsageAudio:
    try:
        usage_audio = TranslationUsageAudio(
            usage_id=usage_id,
            storage_url=storage_url,
            voice_id=voice_id,
            audio_format=audio_format,
        )
        session.add(usage_audio)
        await session.commit()
        return usage_audio

    except IntegrityError:
        print("CAUGHT INTEGRITY ERROR")
        await session.rollback()

        stmt = (
            select(TranslationUsageAudio)
            .where(TranslationUsageAudio.usage_id == usage_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one()
    
#FETCH FROM DATABASE

async def get_existing_audio_for_usage(
    session,
    usage_id: int
) -> LinkResponse | None:
    stmt = (
        select(TranslationUsageAudio)
        .where(TranslationUsageAudio.usage_id == usage_id)
    )

    result = await session.execute(stmt)
    link = result.scalar_one_or_none()

    if not link:
        return None

    print("LINK", link.__dict__)

    return LinkResponse.model_validate({
        "id": link.id,
        "usage_id": usage_id,
        "storage_url": link.storage_url,
        "created_at": link.created_at,
    })


# async def get_translation_with_audio_by_word(
#     session: AsyncSession,
#     word: str,
# ) -> tuple[Translation | None, TranslationAudio | None]:
#     """
#         Get a traslation by word with the audio
        
#         :param session: Description
#         :type session: AsyncSession
#         :param word: Description
#         :type word: str
#         :return: Description
#         :rtype: tuple[Translation | None, TranslationAudio | None]
#     """
#     # Case-insensitive lookup is usually what you want
#     stmt = (
#         select(Translation)
#         .where(Translation.word.ilike(word))
#         .options(selectinload(Translation.usages))
#     )

#     result = await session.execute(stmt)
#     translation = result.scalar_one_or_none()

#     if not translation:
#         return None, None

#     # Get most recent audio (or however you define "current")
#     audio_stmt = (
#         select(TranslationAudio)
#         .where(TranslationAudio.translation_id == translation.id)
#         .order_by(TranslationAudio.created_at.desc())
#         .limit(1)
#     )

#     audio_result = await session.execute(audio_stmt)
#     audio = audio_result.scalar_one_or_none()

#     return translation, audio


# async def get_translation_with_audio_by_id(
#     session: AsyncSession,
#     id: int,
# ) -> tuple[Translation | None, TranslationAudio | None]:
#     """
#         Get a traslation by id with the audio
        
#         :param session: Description
#         :type session: AsyncSession
#         :param word: Description
#         :type id: int
#         :return: Description
#         :rtype: tuple[Translation | None, TranslationAudio | None]
#     """
#     # Case-insensitive lookup is usually what you want
#     #TODO:
#     #It needs to make the join of translation usages to the audio if it exists and then include in the response
#     stmt = (
#         select(Translation)
#         .where(Translation.id==id)
#         .options(selectinload(Translation.usages))
#     )

#     result = await session.execute(stmt)
#     translation = result.scalar_one_or_none()

#     if not translation:
#         return None, None

#     # Get most recent audio (or however you define "current")
#     audio_stmt = (
#         select(TranslationAudio)
#         .where(TranslationAudio.translation_id == translation.id)
#         .order_by(TranslationAudio.created_at.desc())
#         .limit(1)
#     )

#     audio_result = await session.execute(audio_stmt)
#     audio = audio_result.scalar_one_or_none()

#     return translation, audio

async def get_translation_with_audio_by_word(
    session: AsyncSession,
    word: str,
) -> tuple[Translation | None, TranslationAudio | None]:
    # Load translation + usages + usage audio + actual audio
    stmt = (
        select(Translation)
        .where(Translation.word.ilike(word))
        .options(
            selectinload(Translation.usages)
            .selectinload(TranslationUsage.usage_audio)
            .selectinload(TranslationUsageAudio.usage)
        )
    )

    result = await session.execute(stmt)
    translation = result.scalar_one_or_none()

    if not translation:
        return None, None

    # Get the most recent translation audio for the word itself
    audio_stmt = (
        select(TranslationAudio)
        .where(TranslationAudio.translation_id == translation.id)
        .order_by(TranslationAudio.created_at.desc())
        .limit(1)
    )
    audio_result = await session.execute(audio_stmt)
    audio = audio_result.scalar_one_or_none()

    print("THIS IS THE TRANSLATION OBJECT", translation.__dict__)
    for trans_usage in translation.usages:
        print(trans_usage.__dict__)

    return translation, audio

async def get_usages_by_translation_id(
    session: AsyncSession,
    translation_id: int,
) -> list[TranslationUsage]:
    stmt = select(TranslationUsage).where(
        TranslationUsage.translation_id == translation_id
    )

    result = await session.execute(stmt)
    return result.scalars().all()

async def get_translation_with_audio_by_id(
    session: AsyncSession,
    id: int,
) -> tuple[Translation | None, TranslationAudio | None]:
    # Load translation + usages + usage audio + actual audio
    stmt = (
        select(Translation)
        .where(Translation.id == id)
        .options(
            selectinload(Translation.usages)
            .selectinload(TranslationUsage.usage_audio)
            .selectinload(TranslationUsageAudio.usage)
        )
    )

    result = await session.execute(stmt)
    translation = result.scalar_one_or_none()

    if not translation:
        return None, None

    # Get the most recent translation audio for the word itself
    audio_stmt = (
        select(TranslationAudio)
        .where(TranslationAudio.translation_id == translation.id)
        .order_by(TranslationAudio.created_at.desc())
        .limit(1)
    )
    audio_result = await session.execute(audio_stmt)
    audio = audio_result.scalar_one_or_none()

    print("THIS IS THE TRANSLATION OBJECT", translation.__dict__)
    for trans_usage in translation.usages:
        print(trans_usage.__dict__)

    return translation, audio

async def get_usages_by_translation_id(
    session: AsyncSession,
    translation_id: int,
) -> list[TranslationUsage]:
    stmt = select(TranslationUsage).where(
        TranslationUsage.translation_id == translation_id
    )

    result = await session.execute(stmt)
    return result.scalars().all()




async def main():
    # 1️⃣ Read JSON file
    # get project root (parent of current file)
    BASE_DIR = Path(__file__).resolve().parent.parent

    filename = BASE_DIR / "output" / "fart_20260123_084755.json"

    with open(filename, "r", encoding="utf-8") as f:
        payload = json.load(f)

    # # 2️⃣ Create async session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # 3️⃣ Insert translation
        #response = await insert_translation(session, payload)

        #response = await insert_translation_audio(session,1,"https://japanese-translations.nl-ams-1.linodeobjects.com/japanese-translate/0ead6ffb-80f0-4351-8104-97ed96c46fd0.mp3","EXAVITQu4vr4xnSDxMaL")
        
        translation,audio = await get_translation_with_audio_by_id(session,200)
        if translation and audio:
            print(translation.reading,audio)

        if translation and not audio:
            print(translation)


        # 4️⃣ Print the Pydantic response as JSON
        #print(response.json())


if __name__ == "__main__":
    asyncio.run(main())