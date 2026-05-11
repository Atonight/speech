from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


DEFAULT_WEBSOCKET_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/inference"


@dataclass(frozen=True)
class SynthesisResult:
    output_path: Path
    request_id: str | None
    first_package_delay_ms: float | None
    byte_size: int


class CosyVoiceClient:
    """Small wrapper around DashScope CosyVoice TTS."""

    def __init__(
        self,
        *,
        model: str = "cosyvoice-v2",
        websocket_url: str = DEFAULT_WEBSOCKET_URL,
    ) -> None:
        self.model = model
        self.websocket_url = websocket_url

    def synthesize_to_file(
        self,
        *,
        text: str,
        output_path: str | Path,
        voice: str = "longjixin",
        audio_format: str = "WAV_22050HZ_MONO_16BIT",
        volume: int | None = None,
        speech_rate: float | None = None,
        pitch_rate: float | None = None,
        instruction: str | None = None,
        language_hints: list[str] | None = None,
        timeout_millis: int | None = None,
    ) -> SynthesisResult:
        if not text.strip():
            raise ValueError("text must not be empty")

        api_key = os.environ.get("DASHSCOPE_API_KEY")
        if not api_key:
            raise RuntimeError("DASHSCOPE_API_KEY is required but is not set")

        dashscope, SpeechSynthesizer, AudioFormat = self._load_dashscope()
        dashscope.api_key = api_key
        dashscope.base_websocket_api_url = self.websocket_url

        request_params: dict[str, Any] = {
            "model": self.model,
            "voice": voice,
            "format": self._resolve_audio_format(AudioFormat, audio_format),
        }
        if volume is not None:
            request_params["volume"] = volume
        if speech_rate is not None:
            request_params["speech_rate"] = speech_rate
        if pitch_rate is not None:
            request_params["pitch_rate"] = pitch_rate
        if instruction is not None:
            request_params["instruction"] = instruction
        if language_hints is not None:
            request_params["language_hints"] = language_hints

        # DashScope docs require a fresh SpeechSynthesizer for each call.
        synthesizer = SpeechSynthesizer(**request_params)
        if timeout_millis is None:
            audio = synthesizer.call(text)
        else:
            audio = synthesizer.call(text, timeout_millis=timeout_millis)

        if not isinstance(audio, bytes) or not audio:
            raise RuntimeError("CosyVoice returned empty audio data")

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(audio)

        return SynthesisResult(
            output_path=output,
            request_id=synthesizer.get_last_request_id(),
            first_package_delay_ms=synthesizer.get_first_package_delay(),
            byte_size=len(audio),
        )

    def synthesize_many(
        self,
        items: Iterable[tuple[str, str | Path]],
        *,
        voice: str = "longjixin",
        audio_format: str = "WAV_22050HZ_MONO_16BIT",
        volume: int | None = None,
        speech_rate: float | None = None,
        pitch_rate: float | None = None,
        instruction: str | None = None,
        language_hints: list[str] | None = None,
        timeout_millis: int | None = None,
    ) -> list[SynthesisResult]:
        results: list[SynthesisResult] = []
        for text, output_path in items:
            results.append(
                self.synthesize_to_file(
                    text=text,
                    output_path=output_path,
                    voice=voice,
                    audio_format=audio_format,
                    volume=volume,
                    speech_rate=speech_rate,
                    pitch_rate=pitch_rate,
                    instruction=instruction,
                    language_hints=language_hints,
                    timeout_millis=timeout_millis,
                )
            )
        return results

    def compare_voices(
        self,
        *,
        text: str,
        voices: Iterable[str],
        output_dir: str | Path = "outputs/audio",
        file_stem: str = "voice_compare",
        audio_format: str = "WAV_22050HZ_MONO_16BIT",
        volume: int | None = None,
        speech_rate: float | None = None,
        pitch_rate: float | None = None,
        instruction: str | None = None,
        language_hints: list[str] | None = None,
        timeout_millis: int | None = None,
    ) -> list[SynthesisResult]:
        output_root = Path(output_dir)
        results: list[SynthesisResult] = []
        for voice in voices:
            results.append(
                self.synthesize_to_file(
                    text=text,
                    output_path=output_root / f"{file_stem}_{voice}.wav",
                    voice=voice,
                    audio_format=audio_format,
                    volume=volume,
                    speech_rate=speech_rate,
                    pitch_rate=pitch_rate,
                    instruction=instruction,
                    language_hints=language_hints,
                    timeout_millis=timeout_millis,
                )
            )
        return results

    @staticmethod
    def _load_dashscope() -> tuple[Any, Any, Any]:
        try:
            import dashscope
            from dashscope.audio.tts_v2 import AudioFormat, SpeechSynthesizer
        except ImportError as exc:
            raise RuntimeError(
                "dashscope is not installed. Run: pip install -r requirements.txt"
            ) from exc

        return dashscope, SpeechSynthesizer, AudioFormat

    @staticmethod
    def _resolve_audio_format(audio_format_cls: Any, name: str) -> Any:
        try:
            return getattr(audio_format_cls, name)
        except AttributeError as exc:
            raise ValueError(f"Unsupported audio format: {name}") from exc
