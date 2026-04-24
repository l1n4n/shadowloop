# ShadowLoop — Progress

## Current Status: UI improvements applied, pending manual retest

All source modules, Gradio UI, and 57 tests are in place and passing.

## What's Built

- Audio upload + Whisper transcription with word-level timestamps
- Sentence segmentation (punctuation + silence gap detection)
- Segment editing: merge, split, delete (pure functions, re-sequenced IDs)
- Transcript upload as alternative to Whisper (one line = one segment)
- Repeat/pause plan generation
- Audio assembly with pitch-preserving speed change (ffmpeg atempo)
- MP3 export with speed applied
- Gradio 6 UI with three-phase workflow

## UI Improvements (2026-04-24)

1. **Simplified layout** — Added "How it works" intro and plain-language descriptions for each phase. Segment editing tools (merge/split/delete) collapsed into an accordion.
2. **Transcript download** — After transcription, a downloadable .txt file is generated with timestamps (`[0.0s - 1.2s] text`).
3. **Crash fix** — Gradio 6 moved `theme` from `Blocks()` to `launch()`, and removed `show_api`. Fixed both.
4. **HF Spaces deployment** — Created `requirements.txt` and `packages.txt` for Hugging Face Spaces.

## Fixes Applied (from first user test, 2026-04-21)

1. **Merge broken** — Gradio `gr.State` serializes dataclasses to JSON dicts. Added `segments_from_dicts()` reconstitution in all callbacks.
2. **Segments too short** — Silence gap threshold raised 300ms → 600ms, minimum segment duration raised 1000ms → 2000ms.
3. **Speed slider too coarse** — Changed to 0.5–2.0x range, 0.01 step size.
4. **Transcript upload** — Added `segments_from_transcript()` + UI for .txt file upload as alternative to Whisper.

## Known Limitations

- gradio_client 2.5.0 has a State schema bug (TypeError on complex types) — not triggered currently but may resurface if API info is enabled
- Speed change via ffmpeg subprocess (slow for many segments)
- Split uses proportional text split (no word-level precision)
- No per-segment audio preview
- No progress bar during build
- No session persistence (refresh = start over)
- First-run Whisper model download has no progress UI

## Next Steps

- Manual retest of full workflow with new UI
- Deploy to Hugging Face Spaces
- Per-segment audio preview in editor
- Progress feedback during build
