# models.py
from .db import Base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    ForeignKey,
    ForeignKeyConstraint,
    TIMESTAMP,
    func,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import CITEXT


class Translation(Base):
    __tablename__ = "translations"

    id = Column(Integer, primary_key=True, index=True)

    # Source word (English)
    word = Column(CITEXT, nullable=False)

    # Japanese translation
    translation = Column(String(255), nullable=False)

    # Kana reading
    reading = Column(String(255), nullable=True)

    # kanji / kana / mixed / romaji (future-proofed)
    script = Column(String(50), nullable=False)

    created_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False,
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "word",
            "translation",
            "reading",
            name="uq_translation_word_translation_reading",
        ),
    )

    usages = relationship(
        "TranslationUsage",
        back_populates="translation",
        cascade="all, delete-orphan",
    )

    translation_audio = relationship(
        "TranslationAudio",
        back_populates="translation",
        cascade="all, delete-orphan",
    )



class TranslationUsage(Base):
    __tablename__ = "translation_usages"

    id = Column(Integer, primary_key=True)

    translation_id = Column(
        Integer,
        ForeignKey("translations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # English example sentence
    en = Column(Text, nullable=False)

    # Japanese example sentence
    ja = Column(Text, nullable=False)

    created_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False,
    )

    translation = relationship(
        "Translation",
        back_populates="usages",
    )

 
class TranslationAudio(Base):
    __tablename__ = "translation_audio"

    id = Column(Integer, primary_key=True, index=True)

    translation_id = Column(
        Integer,
        ForeignKey("translations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Public S3 / Linode object URL
    storage_url = Column(String(1024), nullable=False)

    # Optional but useful
    voice_id = Column(String(100), nullable=True)
    audio_format = Column(String(20), nullable=False, default="mp3")

    created_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False,
    )

    translation = relationship(
        "Translation",
        back_populates="translation_audio",
    )


class TranslationUsageAudio(Base):
    __tablename__ = "translation_usage_audio"

    id = Column(Integer, primary_key=True)

    usage_id = Column(
        Integer,
        ForeignKey("translation_usages.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    audio_id = Column(
        Integer,
        ForeignKey("translation_audio.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "usage_id",
            "audio_id",
            name="uq_usage_audio",
        ),
    )

    audio = relationship("TranslationAudio")