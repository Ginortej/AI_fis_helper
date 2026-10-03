from hmac import compare_digest

from fastapi import APIRouter, WebSocket

from config.settings import settings
from services.realtime_bridge import bridge_audio


router = APIRouter()


@router.websocket("/ws/esp")
async def esp_audio(websocket: WebSocket) -> None:
    provided_key = websocket.headers.get("x-esp-key")
    if provided_key is None or not compare_digest(provided_key, settings.esp_api_key):
        await websocket.close(code=1008)
        return

    await bridge_audio(websocket, settings)
