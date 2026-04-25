# ShadowLoop — Progress

## Current Status: Deployed to Hugging Face Spaces

All source modules, Gradio UI, and 57 tests are in place and passing.
Live at: https://huggingface.co/spaces/l1n4n/shadowloop

## What's Built

- Audio upload + Whisper transcription with word-level timestamps
- Sentence segmentation (punctuation + silence gap detection)
- Segment editing: merge, split, delete (pure functions, re-sequenced IDs)
- Transcript upload as alternative to Whisper (one line = one segment)
- Repeat/pause plan generation
- Audio assembly with pitch-preserving speed change (ffmpeg atempo)
- MP3 export with speed applied
- Gradio 6 UI with three-phase workflow
- Custom theme + CSS styling

## HF Spaces Deployment (2026-04-25)

1. **Space created** — `l1n4n/shadowloop` on Hugging Face Spaces (Gradio SDK, Python 3.11).
2. **Files deployed** — `app.py`, `requirements.txt`, `packages.txt`, `pyproject.toml`, `src/shadowloop/`, `README.md` (with HF YAML frontmatter).
3. **Module import fix** — HF Spaces installs requirements before copying app files, so `pip install .` fails. Fixed by adding `sys.path.insert(0, "src/")` in `app.py`.
4. **Auth for push** — `hf auth login` required write token. Git push needs token in remote URL since HF Spaces uses HTTPS.

## HF Spaces Deployment Learnings

- `huggingface-cli` is deprecated — use `hf` CLI instead
- `hf repo clone` doesn't exist — use `git clone` directly
- HF Spaces Docker build runs `pip install -r requirements.txt` in a separate stage before app files are copied, so `.` (local install) in requirements.txt fails with "no pyproject.toml found"
- Fix: add `sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))` at top of `app.py`
- Always verify file contents after haiku agent deploys — it can mix up file contents when copying multiple files

## UI Improvements Round 2 (2026-04-24)

1. **Custom Gradio theme** — Warm stone-toned global accent via `gr.themes.Soft()` with custom primary/secondary/neutral hues. Single cohesive color for sliders, inputs, buttons.
2. **Color-coded section titles** — Each phase has a distinct muted color (purple #5b5ea6 Upload, gold #9a7b4f Review, sage #4a8c72 Build). Description text matches title color.
3. **"How it works" color-coded** — Intro text uses `<span>` with matching phase colors.
4. **Compact layout** — Audio + transcript upload side by side. Estimate + build controls in rows. Preview + Download MP3 in one row with `equal_height=True`.
5. **Transcript upload bug fix** — `on_upload_transcript` was not setting `audio_state`, so Build button silently failed. Now returns loaded AudioSegment.
6. **HF Spaces deployment files** — `requirements.txt` and `packages.txt` created.

## Gradio 6 CSS Learnings

- `css` and `theme` params must go in `launch()`, not `Blocks()` constructor
- `show_api` param removed in Gradio 6
- Gradio CSS variables (`--slider_color`, `--color_accent`, etc.) are set at `:root` by the theme — cannot be overridden per-section via CSS custom properties on parent divs
- Per-section component coloring (sliders, inputs) is not achievable via CSS alone — use a single global theme accent instead
- `elem_id` targeting works for Markdown styling; class-based selectors (`.markdown p`) do not reliably reach Svelte-rendered components
- Aggressive CSS overrides on `.block`, `.wrap`, `.gap`, `button`, `input[type=text]` break audio player controls — avoid blanket component-level CSS in Gradio

## UI Improvements Round 1 (2026-04-24)

1. **Simplified layout** — Added "How it works" intro and plain-language descriptions for each phase. Segment editing tools (merge/split/delete) collapsed into an accordion.
2. **Transcript download** — After transcription, a downloadable .txt file is generated with timestamps (`[0.0s - 1.2s] text`).
3. **Crash fix** — Gradio 6 moved `theme` from `Blocks()` to `launch()`, and removed `show_api`. Fixed both.

## Fixes Applied (from first user test, 2026-04-21)

1. **Merge broken** — Gradio `gr.State` serializes dataclasses to JSON dicts. Added `segments_from_dicts()` reconstitution in all callbacks.
2. **Segments too short** — Silence gap threshold raised 300ms → 600ms, minimum segment duration raised 1000ms → 2000ms.
3. **Speed slider too coarse** — Changed to 0.5–2.0x range, 0.01 step size.
4. **Transcript upload** — Added `segments_from_transcript()` + UI for .txt file upload as alternative to Whisper.

## Known Limitations

- gradio_client 2.5.0 has a State schema bug (TypeError on complex types) — not triggered currently but may resurface if API info is enabled
- Per-section component accent colors not possible in Gradio 6 (theme is global)
- Speed change via ffmpeg subprocess (slow for many segments)
- Split uses proportional text split (no word-level precision)
- No per-segment audio preview
- No progress bar during build
- No session persistence (refresh = start over)
- First-run Whisper model download has no progress UI

## Next Steps

- Verify HF Spaces deployment is running correctly
- E2e test on HF Spaces (upload, transcribe, build, download)
- Per-segment audio preview in editor
- Progress feedback during build
