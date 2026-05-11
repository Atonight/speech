from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from cosyvoice_tts import CosyVoiceClient  # noqa: E402


VOICE_PLACEHOLDERS = {"", "YOUR_CLONED_VOICE_ID_OR_SYSTEM_VOICE"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate TTS from SSML files plus a parameter CSV.")
    parser.add_argument("--materials-dir", required=True, help="Directory containing .xml and _instruction.txt files.")
    parser.add_argument("--csv", required=True, help="CSV containing id/model/voice/rate/pitch/volume rows.")
    parser.add_argument("--preset", default="default", help="Preset fallback from configs/presets.yaml.")
    parser.add_argument(
        "--output-dir",
        default=str(PROJECT_ROOT / "outputs" / "audio" / "segments_v35flash_clonea1"),
        help="Output directory. Existing wav files with the same names are overwritten.",
    )
    parser.add_argument("--only-id", default=None, help="Generate only one segment id, e.g. 001.")
    parser.add_argument("--strip-breaks", action="store_true", help="Remove SSML break tags before synthesis.")
    return parser.parse_args()


def load_preset(name: str) -> dict[str, Any]:
    with (PROJECT_ROOT / "configs" / "presets.yaml").open("r", encoding="utf-8") as file:
        presets = yaml.safe_load(file) or {}
    if name not in presets:
        available = ", ".join(sorted(presets))
        raise SystemExit(f"Unknown preset '{name}'. Available presets: {available}")
    return presets[name]


def load_csv_rows(path: Path) -> dict[str, dict[str, str]]:
    rows: list[dict[str, str]] | None = None
    for encoding in ("utf-8-sig", "gb18030", "utf-16"):
        try:
            with path.open("r", encoding=encoding, newline="") as file:
                rows = list(csv.DictReader(file))
            break
        except UnicodeDecodeError:
            continue
    if rows is None:
        raise SystemExit(f"Could not decode CSV file: {path}")
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        segment_id = (row.get("id") or "").strip()
        if not segment_id:
            raise SystemExit(f"CSV row is missing id: {row}")
        result[segment_id] = row
    return result


def load_materials(materials_dir: Path) -> list[tuple[str, Path, Path | None]]:
    xml_files = sorted(materials_dir.glob("*.xml"))
    if not xml_files:
        raise SystemExit(f"No .xml files found in {materials_dir}")

    materials: list[tuple[str, Path, Path | None]] = []
    for xml_path in xml_files:
        segment_id = xml_path.name.split("_", 1)[0]
        instruction_path = xml_path.with_name(f"{xml_path.stem}_instruction.txt")
        materials.append((segment_id, xml_path, instruction_path if instruction_path.exists() else None))
    return materials


def float_or_none(value: str | None) -> float | None:
    if value is None or not value.strip():
        return None
    return float(value)


def int_or_none(value: str | None) -> int | None:
    if value is None or not value.strip():
        return None
    return int(float(value))


def strip_break_tags(text: str) -> str:
    return re.sub(r"<break\b[^>]*/>", "", text, flags=re.IGNORECASE)


def main() -> None:
    args = parse_args()
    preset = load_preset(args.preset)
    csv_rows = load_csv_rows(Path(args.csv))
    materials = load_materials(Path(args.materials_dir))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = []
    if args.only_id:
        materials = [item for item in materials if item[0] == args.only_id]
        if not materials:
            raise SystemExit(f"No segment found for id {args.only_id}")

    for index, (segment_id, xml_path, instruction_path) in enumerate(materials, start=1):
        row = csv_rows.get(segment_id)
        if row is None:
            raise SystemExit(f"No CSV row found for segment id {segment_id} ({xml_path.name})")

        voice = (row.get("voice") or "").strip()
        if voice in VOICE_PLACEHOLDERS:
            voice = preset["voice"]
            model = preset.get("model", "cosyvoice-v3.5-flash")
        else:
            model = (row.get("model") or "").strip() or preset.get("model", "cosyvoice-v3.5-flash")

        text = xml_path.read_text(encoding="utf-8").strip()
        if args.strip_breaks:
            text = strip_break_tags(text)
        if instruction_path is not None:
            instruction = instruction_path.read_text(encoding="utf-8").strip()
        else:
            instruction = (row.get("instruction") or preset.get("instruction") or "").strip()

        output_name = f"{segment_id}.wav" if args.only_id else f"{segment_id}_{segment_id}.wav"
        output_path = output_dir / output_name
        client = CosyVoiceClient(model=model)
        result = client.synthesize_to_file(
            text=text,
            output_path=output_path,
            voice=voice,
            audio_format=preset.get("format", "WAV_22050HZ_MONO_16BIT"),
            volume=int_or_none(row.get("volume")) if row.get("volume") else preset.get("volume"),
            speech_rate=float_or_none(row.get("rate")) if row.get("rate") else preset.get("speech_rate"),
            pitch_rate=float_or_none(row.get("pitch")) if row.get("pitch") else preset.get("pitch_rate"),
            instruction=instruction or None,
            language_hints=preset.get("language_hints"),
        )

        item = {
            "index": index,
            "id": segment_id,
            "xml_path": str(xml_path),
            "instruction_path": str(instruction_path) if instruction_path else None,
            "output_path": str(result.output_path),
            "model": model,
            "voice": voice,
            "rate": float_or_none(row.get("rate")),
            "pitch": float_or_none(row.get("pitch")),
            "volume": int_or_none(row.get("volume")),
            "instruction": instruction,
            "request_id": result.request_id,
            "byte_size": result.byte_size,
        }
        manifest.append(item)
        print(json.dumps(item, ensure_ascii=False))

    manifest_path = output_dir / "manifest_materials.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
