from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from cosyvoice_tts import CosyVoiceClient  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate audio files from a segments JSON file.")
    parser.add_argument("json_path", help="Path to segments JSON.")
    parser.add_argument("--preset", default="default", help="Preset name in configs/presets.yaml.")
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "outputs" / "audio" / "segments_v35flash_clonea1"))
    parser.add_argument("--text-key", default=None, help="Override text field name for segment objects.")
    parser.add_argument("--id-key", default=None, help="Override id field name for segment objects.")
    return parser.parse_args()


def load_preset(name: str) -> dict[str, Any]:
    with (PROJECT_ROOT / "configs" / "presets.yaml").open("r", encoding="utf-8") as file:
        presets = yaml.safe_load(file) or {}
    if name not in presets:
        available = ", ".join(sorted(presets))
        raise SystemExit(f"Unknown preset '{name}'. Available presets: {available}")
    return presets[name]


def load_segments(path: Path) -> list[Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("segments", "items", "data", "rows"):
            value = data.get(key)
            if isinstance(value, list):
                return value
    raise SystemExit("JSON must be a list, or an object with a segments/items/data/rows list.")


def segment_text(segment: Any, text_key: str | None) -> str:
    if isinstance(segment, str):
        return segment.strip()
    if not isinstance(segment, dict):
        raise ValueError(f"Unsupported segment type: {type(segment).__name__}")
    keys = [text_key] if text_key else ["text", "content", "sentence", "line", "script", "ssml"]
    for key in keys:
        if key and isinstance(segment.get(key), str) and segment[key].strip():
            return segment[key].strip()
    raise ValueError(f"Could not find text in segment: {segment}")


def segment_name(segment: Any, index: int, id_key: str | None) -> str:
    if isinstance(segment, dict):
        keys = [id_key] if id_key else ["id", "segment_id", "index", "name"]
        for key in keys:
            value = segment.get(key) if key else None
            if value not in (None, ""):
                return f"{index:03d}_{safe_name(str(value))}"
    return f"{index:03d}"


def safe_name(value: str) -> str:
    allowed = []
    for char in value:
        if char.isalnum() or char in ("-", "_"):
            allowed.append(char)
        else:
            allowed.append("_")
    return "".join(allowed).strip("_") or "segment"


def main() -> None:
    args = parse_args()
    preset = load_preset(args.preset)
    segments = load_segments(Path(args.json_path))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    client = CosyVoiceClient(model=preset.get("model", "cosyvoice-v3.5-flash"))
    manifest = []
    for index, segment in enumerate(segments, start=1):
        text = segment_text(segment, args.text_key)
        name = segment_name(segment, index, args.id_key)
        output_path = output_dir / f"{name}.wav"
        result = client.synthesize_to_file(
            text=text,
            output_path=output_path,
            voice=preset["voice"],
            audio_format=preset.get("format", "WAV_22050HZ_MONO_16BIT"),
            volume=preset.get("volume"),
            speech_rate=preset.get("speech_rate"),
            pitch_rate=preset.get("pitch_rate"),
            instruction=preset.get("instruction"),
            language_hints=preset.get("language_hints"),
        )
        item = {
            "index": index,
            "output_path": str(result.output_path),
            "request_id": result.request_id,
            "byte_size": result.byte_size,
            "text": text,
        }
        manifest.append(item)
        print(json.dumps(item, ensure_ascii=False))

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
