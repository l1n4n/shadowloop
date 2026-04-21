# CLAUDE.md

This file provides guidance to Claude Code for small Python projects that turn audio, video, or text into language-learning practice tools.

Use this as a reusable template for projects such as:
- shadowing practice apps
- listening drill generators
- sentence/phrase loopers
- pronunciation practice tools
- dictation helpers
- transcript-to-practice converters

## How to Use This File

This file is intentionally generic.

It has two layers:
1. a reusable default workflow for similar projects
2. a small `Project Overrides` section for the current repo

When starting a new related repo, keep most of this file and only update the override section.

## Project Overrides

Update this section for the current repository.

- **Current product focus**: audio-first shadowing practice
- **Primary input mode**: uploaded audio
- **Current target behavior**: split source audio into chunked practice units and repeat each chunk with pauses
- **Default repeat count**: 8
- **Preferred UI**: simple local-first Python UI
- **Current deferred features**: cloud backend, accounts, analytics, advanced scoring

If another repo differs, change only these items unless deeper changes are truly necessary.

## Project Philosophy

These projects should optimize for one thing above all else:

**turning source material into useful practice with the fewest possible steps**

The user should not need to understand audio tooling to succeed.

### Primary goals

- simple workflow
- predictable output
- fast iteration
- low setup friction
- clean separation between UI and media logic

### Common non-goals for early versions

Do not add these unless explicitly required:
- user accounts
- cloud backend
- team collaboration
- analytics dashboards
- complex plugin systems
- mobile wrappers
- databases
- background job systems for small local tasks

## Commands

### /advise

Search the repo and existing patterns before starting work.

**When to use**:
- at session start
- before implementing a feature
- before refactoring
- before debugging unfamiliar behavior
- before adding dependencies or new architecture

**Workflow**:

1. Read the user request carefully.
2. Read `README.md`, `CLAUDE.md`, `PRD.docx`, and the files most related to the task.
3. Search for existing modules, utilities, tests, and decision notes.
4. Identify:
   - what already exists
   - what can be reused
   - what is missing
   - the smallest shippable path
   - the main risks or edge cases
5. Return a concise implementation recommendation.

**Expected output shape**:

```text
User: /advise add feature X
Claude:
- Reuse: existing modules Y and Z
- Missing: module A / test B / UI control C
- Risks: edge case D
- Recommended path:
  1. ...
  2. ...
  3. ...
```

### /learn

Save reusable lessons after a meaningful session.

**When to use**:
- after a useful implementation session
- after fixing a tricky bug
- after discovering a good pattern
- before ending a substantial work session

**Workflow**:

1. Read the relevant conversation and changed files.
2. Extract:
   - objective
   - context
   - what worked
   - what failed
   - key thresholds, defaults, or parameters
   - follow-up recommendations
3. Save a concise note to:
   - `docs/learnings/YYYY-MM-DD-<topic>.md`
4. If the change is architectural, also write or update a decision note in:
   - `docs/decisions/`
5. If user-facing behavior changed, update `README.md`.

**Suggested learning note format**:

```text
# <topic>

- Objective
- Context
- What worked
- What failed
- Parameters / thresholds
- Recommended default
- Next step
```

## Key Development Principles

Keep these principles across all similar projects:

1. **KISS** — Keep the implementation simple.
2. **YAGNI** — Do not add features before they are needed.
3. **TDD** — Write tests to drive implementation where practical.
4. **DRY** — Do not duplicate logic or data transformations.
5. **SOLID** — Use only when it improves clarity, not ceremony.
6. **Modularity** — Build independent modules with clear interfaces.
7. **POLA** — Prefer behavior that does not surprise users.

## Default Technical Direction

Unless the repo already uses something else, prefer:

- Python 3.11+
- a simple local-first UI
- modular media-processing code
- thin adapters around external tools/services
- pytest for tests
- a small dependency set

### Default stack choices by project type

For local media-learning tools, these are usually reasonable defaults:
- **UI**: Gradio or another minimal Python UI
- **Audio assembly**: pydub
- **Media conversion**: ffmpeg
- **Transcription**: whisper or faster-whisper when needed
- **TTS**: add only if the project actually needs text-to-speech

Do not treat these as mandatory if the repo already has a better fit.

## Architecture Guidance

Prefer a small modular design.

### Recommended generic structure

```text
<project-root>/
  app.py                     # UI entrypoint
  pyproject.toml
  README.md
  CLAUDE.md
  src/<package_name>/
    __init__.py
    config.py                # dataclasses / defaults
    ingest.py                # load/normalize source input
    segmenter.py             # split into units / chunks / sentences
    planner.py               # repetition / pause / sequencing rules
    builder.py               # assemble output media
    exporters.py             # save result files
    transcription.py         # optional
    tts.py                   # optional
    ui_helpers.py            # validation / formatting helpers
  tests/
    test_ingest.py
    test_segmenter.py
    test_planner.py
    test_builder.py
    test_exporters.py
```

### Separation of concerns

- `ingest` should only load and normalize input.
- `segmenter` should only detect or derive practice units.
- `planner` should convert units + settings into a repeat/pause sequence.
- `builder` should assemble final output.
- `transcription` and `tts` should remain optional and isolated.
- UI code should stay thin and call reusable functions.

## Product Scope Pattern

For similar projects, scope work in layers.

### MVP

Build the smallest version that creates useful practice output.

Typical MVP responsibilities:
- accept one clear input mode
- split or detect practice units
- let the user review/edit units when practical
- apply repetition/pause rules
- generate downloadable output

### V2

Improve quality and usability:
- better editing controls
- better progress/error messages
- optional second input mode
- transcript or metadata assistance

### V3

Only after the core workflow is reliable:
- advanced comparison features
- scoring
- cloud sync
- collaboration
- heavy automation

## Core Output Contract

Every repo in this family should make the output rule explicit.

Examples:
- repeat each sentence N times with pauses
- loop each phrase with a response gap
- alternate model audio and user recording slots

For the current repo override, the rule is:

```text
for chunk in chunks:
    repeat chunk audio N times
    insert short pause between repeats
    insert longer pause before next chunk
```

Default current-repo settings:
- repeat count: 8
- pause between repeats: 800 ms
- pause between chunks: 1800 ms

## Input Strategy

Similar projects usually support one or more of these:
- audio input
- video input
- transcript input
- plain text input

Rule of thumb:
- start with one primary input mode
- make it reliable
- add other inputs later

For the current repo override:
- audio is first
- video is later
- text/TTS is later

## UX Rules

The user should be able to complete the main flow without documentation.

General UX expectations:
- one obvious primary action per step
- clear control labels
- visible defaults
- editable intermediate results where errors are likely
- obvious download/playback result

Typical workflow shape:
1. provide input
2. detect or prepare units
3. review/edit units
4. generate practice output
5. preview result
6. download result

Avoid exposing internal jargon unless it meaningfully helps the user.

## Development Priorities

When making tradeoffs, prefer:

1. correct core behavior
2. simple and predictable output
3. easy manual correction where automation is imperfect
4. fast iteration speed
5. low dependency complexity
6. advanced features

## Claude Code Workflow

When implementing or modifying something in one of these repos:

1. Read `README.md`, `CLAUDE.md`, `pyproject.toml`, and the most relevant files.
2. Restate the smallest shippable change.
3. Reuse existing code before adding new abstractions.
4. Make the minimum necessary edits.
5. Add or update tests for behavior changes.
6. Run relevant tests and formatting checks.
7. Summarize what changed, tradeoffs made, and the next sensible step.

### Before coding

Check for:
- existing utilities that already solve the problem
- duplicate logic that should be shared
- whether the request belongs in MVP or a later phase
- whether a simpler path already exists

### While coding

- keep functions small
- prefer pure functions for planning and transformation logic
- isolate external tools behind thin adapters
- avoid premature abstractions
- avoid introducing new frameworks without a strong reason

### After coding

Always update one or more of:
- tests
- README usage notes
- docstrings/comments where behavior is non-obvious
- `docs/learnings/` when the session produced reusable lessons

## Coding Standards

### Style expectations

- use type hints on public functions
- prefer dataclasses for user-configurable settings
- prefer explicit names over short names
- handle errors with actionable user-facing messages
- avoid hidden globals
- keep side effects at the edges of the program

### Design expectations

- separate UI from core processing logic
- separate input normalization from segmentation
- separate sequencing rules from output assembly
- keep optional features isolated
- prefer understandable code over clever code

## Testing Guidance

Write tests for the behavior most likely to break.

### Usually worth testing

- input normalization
- segmentation or sentence/chunk boundary behavior
- repeat/pause plan generation
- output assembly order and basic duration expectations
- exporter success
- edge cases around empty or malformed inputs

### Prefer unit tests for

- cleanup/normalization
- boundary rules
- repeat/pause planning
- validation helpers
- filename sanitization

### Prefer integration tests for

- the main end-to-end path from input to output file

Do not over-test third-party libraries. Test repo logic.

## Performance Guidance

- avoid recomputing unchanged intermediate results
- cache when it improves local iteration speed
- keep memory use reasonable for medium-sized inputs
- surface progress for longer jobs
- optimize only after the core workflow works

## Safety and Reliability

- validate user-provided numeric inputs
- reject obviously empty jobs early
- preserve user edits to intermediate units/chunks when possible
- fail clearly when required dependencies are missing
- never silently drop meaningful content without explaining why

## Decision Log Convention

For meaningful architectural choices, create a short note in:

```text
docs/decisions/YYYY-MM-DD-short-title.md
```

Suggested structure:
- context
- decision
- alternatives considered
- consequences

Keep these short.

## What Claude Should Avoid

- rewriting large parts of the app for small requests
- introducing databases for simple local settings
- adding plugin systems too early
- mixing UI logic with processing logic
- building background worker systems for short local jobs
- adding hidden defaults that change output unpredictably
- solving future hypothetical requirements before the current milestone works

## Definition of Done

A task is done when:
- the requested behavior works
- tests cover the new or changed logic
- the UI stays simple
- docs are updated if usage changed
- no unnecessary complexity was added

## Default Assumptions

If the repo does not specify otherwise, assume:
- local-first execution is preferred
- the main workflow should be usable by non-technical users
- one reliable input mode is better than many fragile ones
- intermediate outputs should be editable where automation is error-prone
- advanced features come after the first successful end-to-end path