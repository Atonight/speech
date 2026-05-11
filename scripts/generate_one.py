from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from cosyvoice_tts import CosyVoiceClient  # noqa: E402


DEFAULT_TEXT = "这是一段短视频配音测试。你好，我是龙季新。"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate one CosyVoice audio file.")
    parser.add_argument("--text", default=DEFAULT_TEXT, help="Text or SSML to synthesize.")
    parser.add_argument("--voice", default=None, help="CosyVoice voice, e.g. longjixin.")
    parser.add_argument("--model", default=None, help="Override preset model.")
    parser.add_argument("--instruction", default=None, help="Voice prompt instruction for supported models.")
    parser.add_argument("--preset", default="default", help="Preset name in configs/presets.yaml.")
    parser.add_argument("--output", default=None, help="Output WAV path.")
    parser.add_argument("--timeout-millis", type=int, default=None)
    return parser.parse_args()


def load_preset(name: str) -> dict:
    preset_path = PROJECT_ROOT / "configs" / "presets.yaml"
    with preset_path.open("r", encoding="utf-8") as file:
        presets = yaml.safe_load(file) or {}
    if name not in presets:
        available = ", ".join(sorted(presets))
        raise SystemExit(f"Unknown preset '{name}'. Available presets: {available}")
    return presets[name]


def main() -> None:
    args = parse_args()
    preset = load_preset(args.preset)

    voice = args.voice or preset.get("voice", "longjixin")
    output = Path(args.output) if args.output else PROJECT_ROOT / "outputs" / "audio" / f"{voice}_test.wav"

    instruction = args.instruction if args.instruction is not None else preset.get("instruction")
    language_hints = preset.get("language_hints")

    client = CosyVoiceClient(model=args.model or preset.get("model", "cosyvoice-v2"))
    try:
        result = client.synthesize_to_file(
            text=args.text,
            output_path=output,
            voice=voice,
            audio_format=preset.get("format", "WAV_22050HZ_MONO_16BIT"),
            volume=preset.get("volume"),
            speech_rate=preset.get("speech_rate"),
            pitch_rate=preset.get("pitch_rate"),
            instruction=instruction,
            language_hints=language_hints,
            timeout_millis=args.timeout_millis,
        )
    except RuntimeError as exc:
        raise SystemExit(f"Error: {exc}") from exc

    print(f"Generated: {result.output_path}")
    print(f"Bytes: {result.byte_size}")
    print(f"Request ID: {result.request_id}")
    print(f"First package delay: {result.first_package_delay_ms} ms")


if __name__ == "__main__":
    main()
