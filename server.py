import asyncio
import tempfile
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from doubaoime_asr import (
    transcribe,
    transcribe_stream,
    transcribe_realtime,
    ASRConfig,
    ASRResponse,
    ResponseType,
)

CREDENTIAL_DIR = Path("/app/credentials")
CREDENTIAL_DIR.mkdir(parents=True, exist_ok=True)

config = ASRConfig(credential_path=str(CREDENTIAL_DIR / "credentials.json"))

app = FastAPI(title="Doubao ASR Server", version="0.1.0")


class TranscribeResponse(BaseModel):
    success: bool
    text: str = ""
    error: str = ""


@app.post("/transcribe")
async def transcribe_api(file: UploadFile = File(...)) -> TranscribeResponse:
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            result = await transcribe(tmp_path, config=config)
            return TranscribeResponse(success=True, text=result)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    except Exception as e:
        return TranscribeResponse(success=False, error=str(e))


@app.websocket("/stream")
async def stream_api(ws: WebSocket):
    await ws.accept()
    try:
        # 接收完整音频数据，然后流式返回识别结果
        audio_data = bytearray()
        while True:
            chunk = await ws.receive_bytes()
            audio_data.extend(chunk)

    except WebSocketDisconnect:
        pass

    if not audio_data:
        return

    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(bytes(audio_data))
            tmp_path = tmp.name

        try:
            async for resp in transcribe_stream(tmp_path, config=config):
                await ws.send_json({
                    "type": resp.type.name,
                    "text": resp.text,
                    "is_final": resp.is_final,
                    "error": resp.error_msg,
                })
                if resp.type == ResponseType.ERROR:
                    break
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    except Exception as e:
        try:
            await ws.send_json({"type": "ERROR", "error": str(e)})
        except Exception:
            pass


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
