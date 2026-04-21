# ShadowLoop — Progress

## Current Status: MVP code-complete, pending e2e retest

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

## Fixes Applied (from first user test, 2026-04-21)

1. **Merge broken** — Gradio `gr.State` serializes dataclasses to JSON dicts. Added `segments_from_dicts()` reconstitution in all callbacks.
2. **Segments too short** — Silence gap threshold raised 300ms → 600ms, minimum segment duration raised 1000ms → 2000ms.
3. **Speed slider too coarse** — Changed to 0.5–2.0x range, 0.01 step size.
4. **Transcript upload** — Added `segments_from_transcript()` + UI for .txt file upload as alternative to Whisper.

## Known Limitations

- Speed change via ffmpeg subprocess (slow for many segments)
- Split uses proportional text split (no word-level precision)
- No per-segment audio preview
- No progress bar during build
- No session persistence (refresh = start over)
- First-run Whisper model download has no progress UI

## Next Steps

- Retest full workflow after fixes
- Per-segment audio preview in editor
- Progress feedback during build
