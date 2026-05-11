# AGENTS.md

## Project Purpose

This repository manages Chinese short-video voice-over assets and calls Alibaba Cloud DashScope CosyVoice to generate narration audio.

## Rules

- Never hard-code API keys. Read `DASHSCOPE_API_KEY` from the environment.
- Keep application code under `src/cosyvoice_tts/`.
- Keep `scripts/` files as thin command-line wrappers.
- Write generated audio to `outputs/audio/`.
- Do not commit generated audio files.
- Prefer editable configuration in `configs/voices.yaml` and `configs/presets.yaml`.

## Common Commands

```bash
pip install -r requirements.txt
python scripts/generate_one.py
```
