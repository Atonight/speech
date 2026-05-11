from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from cosyvoice_tts.voice_design import VoiceDesignClient  # noqa: E402


DEFAULT_PROMPT = (
    "年轻中文普通话女声，自拍视频口播感，声音自然、生活化、低表演感。"
    "语气平实，轻微无语，带一点自嘲和吐槽感，像普通人面对镜头复述一件离谱但真实的经历。"
    "不要播音腔，不要甜美客服感，不要元气少女感，不要电台旁白感，不要夸张脱口秀感。"
    "语速中等偏快，句尾自然收住，情绪克制但有真实感，适合抖音家庭故事类短视频口播。"
)

DEFAULT_PREVIEW_TEXT = (
    "大家都以为，江浙沪独生女，拿的都是爽文剧本，对吧？"
    "但我大二那年，在自己家，因为一条窗帘没有绑出标准的褶皱，被我亲爹打到报警。"
    "不好意思，我拿的不是爽文，是家庭边界恐怖片。"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create CosyVoice voice-design previews.")
    parser.add_argument("--target-model", default="cosyvoice-v3-flash")
    parser.add_argument("--voice-prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--preview-text", default=DEFAULT_PREVIEW_TEXT)
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--prefix", default="vlogvox")
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "outputs" / "audio" / "voice_design"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    client = VoiceDesignClient()
    output_dir = Path(args.output_dir)
    results = []

    for index in range(1, args.count + 1):
        result = client.create_voice(
            target_model=args.target_model,
            voice_prompt=args.voice_prompt,
            preview_text=args.preview_text,
            prefix=args.prefix,
            output_dir=output_dir,
        )
        item = {
            "index": index,
            "voice_id": result.voice_id,
            "preview_path": str(result.preview_path),
            "request_id": result.request_id,
            "byte_size": result.byte_size,
            "target_model": args.target_model,
        }
        results.append(item)
        print(json.dumps(item, ensure_ascii=False))

    manifest_path = output_dir / "voice_design_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "voice_prompt": args.voice_prompt,
                "preview_text": args.preview_text,
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
