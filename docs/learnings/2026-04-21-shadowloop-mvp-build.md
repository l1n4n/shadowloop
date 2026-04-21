# ShadowLoop MVP Build Session

## Objective
Build the core ShadowLoop app from greenfield — audio upload → Whisper segmentation → sentence editing → repeat/pause assembly → MP3 export, with a Gradio UI.

## Context
- Greenfield repo with only CLAUDE.md and PRD.docx
- Started with Python 3.9.7, later switched to Python 3.11 venv for compatibility
- PRD describes a full mobile app; CLAUDE.md scopes to local-first Python MVP

## What Worked
- Fanning out 5 haiku agents in parallel to build all modules simultaneously — total wall time ~9 minutes for 6 source modules + 4 test files
- Writing config.py and __init__.py first (by hand) so agents had stable types to import
- Pure-function design for planner and segment editing — made testing trivial (51 tests, all pass in 1s)
- Using mock objects (MockWord, MockSegment) in segmenter tests to avoid needing a real Whisper model
- Keeping Segment as timestamps-only (no audio reference) — clips sliced on demand from source AudioSegment

## What Failed
- `pip install -e ".[dev]"` failed because pip 21.2.4 doesn't support PEP 660 editable installs with pyproject.toml-only projects. Fixed by creating a Python 3.11 venv (which ships with modern pip).
- Haiku agent produced a merge_segments bug: hardcoded `id=0` on the merged Segment instead of using the running `new_id` counter. Caught during code review before tests ran.
- Haiku agent wrote a test (`test_merge_resequences_ids`) that asserted the buggy behavior (`result[1].id == 0`). Agent-generated tests can encode bugs as expected behavior — always review both code and tests together.
- Originally used `faster-whisper` in the plan, but user installed `openai-whisper` instead. Different API (dict-based vs object-based). Had to rewrite `transcribe()` to wrap openai-whisper output in SimpleNamespace objects to keep the same `.word`/`.start`/`.end` attribute interface used by `_split_into_sentences()`.
- Gradio 4.44.1 has a critical bug in `gradio-client` 1.3.0: `json_schema_to_python_type` crashes with `TypeError: argument of type 'bool' is not iterable` when serializing pydantic schemas. Affects `gr.Audio`, `gr.File`, `gr.Dataframe`, and `gr.State` components. Tried: removing `datatype` param, replacing `gr.Dataframe` with `gr.HTML`, upgrading `gradio-client` alone (breaks import). Fix: upgrade to Gradio 6.x which bundles a fixed client.
- `app.launch()` fails with "localhost is not accessible" on this machine. Fix: `app.launch(server_name="0.0.0.0")`.

## Parameters / Thresholds
- Sentence boundary: silence gap >= 300ms or sentence-ending punctuation (.!?)
- Minimum segment duration: 1000ms (shorter segments merged with neighbor)
- Clip padding: 50ms on each boundary (clamped to audio bounds)
- Defaults: 8 repeats, 2.5s repeat pause, 4s sentence pause, 1.0x speed
- Speed change: ffmpeg atempo filter (0.5-2.0 range, pitch-preserving)

## Recommended Defaults
- Use Python 3.11+ venv for this project (`python3.11 -m venv .venv`)
- Use Gradio >= 6.0 (4.44.1 has a critical schema serialization bug)
- Use `openai-whisper` (not `faster-whisper`) — already installed and working
- For parallel agent builds: always write shared types (dataclasses, interfaces) by hand first
- Always review haiku-generated code for ID/counter bugs in list-rebuilding functions
- When specifying whisper library in deps, be explicit: `openai-whisper` vs `faster-whisper` are different packages with different APIs

## Next Steps
- Run full end-to-end test with pitch.mp3 now that Gradio 6 is installed
- Add progress feedback during build (gr.Progress)
- Add per-segment audio preview in the editor
- Consider storing word-level timestamps in Segment for better split accuracy
