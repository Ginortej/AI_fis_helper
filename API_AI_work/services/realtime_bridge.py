import asyncio
import base64
import json
import logging
from urllib.parse import urlencode

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect, WebSocketState
from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import ConnectionClosed

from config.settings import Settings


logger = logging.getLogger(__name__)
MAX_AUDIO_FRAME = 64 * 1024


def session_update(settings: Settings) -> dict:
    return {
        "type": "session.update",
        "session": {
            "type": "realtime",
            "model": settings.realtime_model,
            "output_modalities": ["audio"],
            "audio": {
                "input": {
                    "format": {"type": "audio/pcm", "rate": 24000},
                    "turn_detection": {
                        "type": "server_vad",
                        "create_response": True,
                        "interrupt_response": True,
                    },
                },
                "output": {
                    "format": {"type": "audio/pcm", "rate": 24000},
                    "voice": settings.realtime_voice,
                },
            },
        },
    }


async def esp_to_openai(esp: WebSocket, upstream: ClientConnection) -> None:
    while True:
        message = await esp.receive()
        if message["type"] == "websocket.disconnect":
            return

        audio = message.get("bytes")
        if audio is None:
            # Audio is the only supported client payload. Ignore text frames.
            continue
        if not audio or len(audio) > MAX_AUDIO_FRAME or len(audio) % 2:
            await esp.send_json({"type": "error", "message": "Invalid PCM16 audio frame"})
            continue

        await upstream.send(json.dumps({
            "type": "input_audio_buffer.append",
            "audio": base64.b64encode(audio).decode("ascii"),
        }))


async def openai_to_esp(upstream: ClientConnection, esp: WebSocket) -> None:
    async for raw in upstream:
        event = json.loads(raw)
        event_type = event.get("type")

        if event_type == "response.output_audio.delta":
            await esp.send_bytes(base64.b64decode(event["delta"], validate=True))
        elif event_type == "input_audio_buffer.speech_started":
            # ESP must discard audio it has queued for playback on interruption.
            await esp.send_json({"type": "clear_playback"})
        elif event_type == "response.output_audio.done":
            await esp.send_json({"type": "audio_done"})
        elif event_type == "error":
            logger.warning("OpenAI Realtime error: %s", event.get("error", {}).get("code"))
            await esp.send_json({"type": "error", "message": "Realtime session error"})


async def bridge_audio(esp: WebSocket, settings: Settings) -> None:
    if not settings.token_api_ai:
        logger.error("TOKEN_API_AI is not configured")
        await esp.close(code=1011)
        return

    url = "wss://api.openai.com/v1/realtime?" + urlencode({"model": settings.realtime_model})
    try:
        async with connect(
            url,
            additional_headers={"Authorization": f"Bearer {settings.token_api_ai}"},
            max_size=4 * 1024 * 1024,
            ping_interval=20,
            open_timeout=10,
        ) as upstream:
            await upstream.send(json.dumps(session_update(settings)))
            await esp.accept()
            await esp.send_json({"type": "ready", "format": "pcm16", "sample_rate": 24000, "channels": 1})

            tasks = {
                asyncio.create_task(esp_to_openai(esp, upstream)),
                asyncio.create_task(openai_to_esp(upstream, esp)),
            }
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            for task in done:
                task.result()
    except (WebSocketDisconnect, ConnectionClosed):
        pass
    except Exception:
        logger.exception("Audio bridge stopped unexpectedly")
        if esp.application_state == WebSocketState.CONNECTED:
            try:
                await esp.send_json({"type": "error", "message": "Audio bridge unavailable"})
            except RuntimeError:
                pass
    finally:
        if esp.application_state == WebSocketState.CONNECTED:
            try:
                await esp.close()
            except RuntimeError:
                pass
        elif esp.application_state == WebSocketState.CONNECTING:
            await esp.close(code=1011)
