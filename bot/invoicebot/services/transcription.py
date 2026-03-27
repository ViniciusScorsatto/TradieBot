from __future__ import annotations

from pathlib import Path

import httpx


OPENAI_TRANSCRIPT_URL = "https://api.openai.com/v1/audio/transcriptions"


async def transcribe_audio_file(audio_path: str, api_key: str) -> str:
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(audio_path)

    async with httpx.AsyncClient(timeout=60.0) as client:
        with path.open("rb") as audio_file:
            response = await client.post(
                OPENAI_TRANSCRIPT_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                data={
                    "model": "whisper-1",
                    "response_format": "text",
                },
                files={"file": (path.name, audio_file, "audio/ogg")},
            )
        response.raise_for_status()
        return response.text.strip()
