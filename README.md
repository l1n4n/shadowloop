---
title: ShadowLoop
emoji: 🔁
colorFrom: gray
colorTo: green
sdk: gradio
sdk_version: 6.13.0
app_file: app.py
python_version: "3.11"
pinned: false
---

# ShadowLoop

Local sentence-level repetition trainer for English shadowing practice. Upload audio, review sentence segments, configure repeats and pauses, download a practice MP3.

## Requirements

- Python 3.11+
- ffmpeg (`sudo apt install ffmpeg` or `brew install ffmpeg`)

## Install

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

First run will download the Whisper `base` model (~140 MB).

## Usage

```bash
source .venv/bin/activate
python app.py
```

Open the URL shown in the terminal (typically `http://0.0.0.0:7860`).

### Workflow

1. **Upload** an audio file and click **Transcribe** (or upload a `.txt` transcript instead)
2. **Review** the detected sentences — merge, split, or delete as needed
3. **Configure** repeat count, pauses, and playback speed
4. Click **Build Practice Audio**, preview, and download the MP3

### Settings

| Setting | Default | Range |
|---|---|---|
| Repeat count | 8 | 1–20 |
| Pause between repeats | 2.5s | 0–10s |
| Pause between sentences | 4s | 1–15s |
| Playback speed | 1.0x | 0.5x–2.0x |

Speed is applied to the exported MP3 (pitch-preserving via ffmpeg atempo).

## Tests

```bash
python -m pytest
```

## Project Structure

```
app.py                        # Gradio UI
src/shadowloop/
    config.py                 # Segment + ShadowingConfig dataclasses
    ingest.py                 # Audio loading and normalization
    segmenter.py              # Whisper transcription + sentence splitting + edit ops
    planner.py                # Repeat/pause plan generation
    builder.py                # Audio assembly with speed change
    exporters.py              # MP3 export
tests/
    test_config.py
    test_segmenter.py
    test_planner.py
    test_builder.py
```
