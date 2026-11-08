
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel
from fastapi import HTTPException
from researcher import research_product


app = FastAPI(title="Price Scout AI")
@app.post("/api/atlas/speak")
def price_scout_atlas_speak(payload: dict):
    import os
    import requests
    from pathlib import Path
    from dotenv import load_dotenv
    from fastapi import HTTPException
    from fastapi.responses import Response

    load_dotenv(
        dotenv_path=Path(__file__).resolve().parent / ".env"
    )

    api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID")

    if not api_key or not voice_id:
        raise HTTPException(
            status_code=503,
            detail="Atlas voice is not configured."
        )

    message = str(payload.get("text", "")).strip()

    if not message or len(message) > 5000:
        raise HTTPException(
            status_code=400,
            detail="Narration must contain 1 to 5000 characters."
        )

    try:
        result = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={
                "xi-api-key": api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
            json={
                "text": message,
                "model_id": "eleven_flash_v2_5",
            },
            timeout=45,
        )
        result.raise_for_status()
    except requests.RequestException:
        raise HTTPException(
            status_code=502,
            detail="ElevenLabs could not generate Atlas speech."
        )

    return Response(
        content=result.content,
        media_type="audio/mpeg"
    )

BASE_DIR = Path(__file__).resolve().parent

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)


@app.get("/")
def home():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "Price Scout AI"}

class ResearchRequest(BaseModel):
    product: str


@app.post("/api/research")
def research(request: ResearchRequest):
    product = request.product.strip()

    if not product:
        raise HTTPException(
            status_code=400,
            detail="Please enter a product name."
        )

    if len(product) > 200:
        raise HTTPException(
            status_code=400,
            detail="Product name is too long."
        )

    try:
        
        data = research_product(product)

        return {
            "product": product,
            "research": data
        }

    except Exception:
        import traceback
        traceback.print_exc()

        raise HTTPException(
            status_code=502,
            detail="AI research failed. Check the server terminal."
        )
