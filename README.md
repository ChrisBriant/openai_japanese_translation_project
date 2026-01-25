# English to Japanese Speech Translation API

A Python-based backend service that translates English words into Japanese using OpenAI, generates high-quality Japanese speech using ElevenLabs, and stores the results in a database with audio files hosted in an S3-compatible bucket.

The service exposes secure REST API endpoints protected by a secret API key.

---

## Features

- 🇯🇵 Translate English words into natural Japanese
- 🧠 Powered by OpenAI for accurate translations
- 🔊 Generate Japanese speech using ElevenLabs
- ☁️ Store audio files in an S3 bucket
- 🗄️ Persist translations and metadata in a database
- 🔐 Secure REST API access using a secret key
- ⚡ Async-friendly and scalable design

---

## Architecture Overview

Client
↓
REST API (API Key Auth)
↓
OpenAI → Japanese Translation
↓
ElevenLabs → Speech Generation
↓
S3 Bucket (Audio Storage)
↓
Database (Translation Metadata)

## Tech Stack

- **Python 3.10+**
- **OpenAI API** – translation
- **ElevenLabs API** – text-to-speech
- **FastAPI** (or Flask) – REST API
- **PostgreSQL / SQLite** – persistence layer
- **AWS S3** (or compatible storage) – audio file storage
- **SQLAlchemy** (optional) – ORM
- **Docker** (optional) – deployment

---

## Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_key
ELEVENLABS_API_KEY=your_elevenlabs_key

AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=eu-west-1
S3_BUCKET_NAME=your_bucket_name

API_SECRET_KEY=your_api_secret

DATABASE_URL=sqlite:///./app.db
# or postgres://user:password@host:port/dbname

## Voice IDs

- EXAVITQu4vr4xnSDxMaL