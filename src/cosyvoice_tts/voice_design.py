from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_CUSTOMIZATION_URL = "https://dashscope.aliyuncs.com/api/v1/services/audio/tts/customization"


@dataclass(frozen=True)
class VoiceDesignResult:
    voice_id: str
    preview_path: Path
    request_id: str | None
    byte_size: int


class VoiceDesignClient:
    def __init__(self, *, url: str = DEFAULT_CUSTOMIZATION_URL) -> None:
        self.url = url

    def create_voice(
        self,
        *,
        target_model: str,
        voice_prompt: str,
        preview_text: str,
        prefix: str,
        output_dir: str | Path,
        sample_rate: int = 24000,
        response_format: str = "wav",
    ) -> VoiceDesignResult:
        api_key = os.environ.get("DASHSCOPE_API_KEY")
        if not api_key:
            raise RuntimeError("DASHSCOPE_API_KEY is required but is not set")

        payload = {
            "model": "voice-enrollment",
            "input": {
                "action": "create_voice",
                "target_model": target_model,
                "voice_prompt": voice_prompt,
                "preview_text": preview_text,
                "prefix": prefix,
            },
            "parameters": {
                "sample_rate": sample_rate,
                "response_format": response_format,
            },
        }

        request = urllib.request.Request(
            self.url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                result: dict[str, Any] = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Voice design request failed with HTTP {exc.code}: {body}") from exc

        output = result.get("output", {})
        voice_id = output.get("voice_id")
        audio_data = output.get("preview_audio", {}).get("data")
        if not voice_id or not audio_data:
            raise RuntimeError(f"Unexpected voice design response: {json.dumps(result, ensure_ascii=False)}")

        audio_bytes = base64.b64decode(audio_data)
        output_root = Path(output_dir)
        output_root.mkdir(parents=True, exist_ok=True)
        preview_path = output_root / f"{voice_id}_preview.{response_format}"
        preview_path.write_bytes(audio_bytes)

        return VoiceDesignResult(
            voice_id=voice_id,
            preview_path=preview_path,
            request_id=result.get("request_id"),
            byte_size=len(audio_bytes),
        )
