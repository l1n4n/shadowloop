"""
CLI tool for ShadowLoop — turns audio into shadowing practice files.
source .venv/bin/activate
Usage:
    python shadowloop_cli.py input.mp3 output.mp3
    python shadowloop_cli.py input.wav output.mp3 --repeats 5 --speed 0.8
    python shadowloop_cli.py input.mp3 output.mp3 --transcript lines.txt
"""

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from shadowloop.ingest import check_ffmpeg, load_audio, prepare_for_transcription, export_temp_wav
from shadowloop.segmenter import segment_audio, segments_from_transcript
from shadowloop.planner import build_plan, estimate_duration_ms
from shadowloop.builder import build_audio
from shadowloop.exporters import export_mp3, export_transcript
from shadowloop.config import ShadowingConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate shadowing practice audio from a source file."
    )
    parser.add_argument("input", help="Path to source audio file")
    parser.add_argument("output", help="Path for output MP3 file")
    parser.add_argument(
        "--repeats", type=int, default=3,
        help="Times each segment is repeated (default: 3)"
    )
    parser.add_argument(
        "--pause-between-repeats", type=int, default=2500,
        help="Silence between repeats in ms (default: 2500)"
    )
    parser.add_argument(
        "--pause-between-segments", type=int, default=3000,
        help="Silence between segments in ms (default: 3000)"
    )
    parser.add_argument(
        "--speed", type=float, default=1.0,
        help="Playback speed 0.5-2.0 (default: 1.0)"
    )
    parser.add_argument(
        "--whisper-model", default="base",
        help="Whisper model size: tiny, base, small, medium, large (default: base)"
    )
    parser.add_argument(
        "--transcript", default=None,
        help="Path to transcript .txt file (one line per segment). Skips Whisper."
    )
    return parser.parse_args()


def format_duration(ms: int) -> str:
    seconds = ms // 1000
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}m {secs}s"


def main() -> None:
    args = parse_args()

    check_ffmpeg()

    config = ShadowingConfig(
        repeat_count=args.repeats,
        pause_between_repeats_ms=args.pause_between_repeats,
        pause_between_sentences_ms=args.pause_between_segments,
        playback_speed=args.speed,
    )
    errors = config.validate()
    if errors:
        for e in errors:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Load audio
    print(f"Loading {args.input} ...")
    audio = load_audio(args.input)
    duration_ms = len(audio)
    print(f"  Duration: {format_duration(duration_ms)}")

    # Segment
    if args.transcript:
        print(f"Reading transcript from {args.transcript} ...")
        with open(args.transcript) as f:
            text = f.read()
        segments = segments_from_transcript(text, duration_ms)
    else:
        print(f"Transcribing with Whisper ({args.whisper_model}) ...")
        mono = prepare_for_transcription(audio)
        wav_path = export_temp_wav(mono)
        try:
            segments = segment_audio(wav_path, duration_ms, args.whisper_model)
        finally:
            os.unlink(wav_path)

        transcript_path = os.path.splitext(args.output)[0] + ".txt"
        export_transcript(segments, transcript_path)
        print(f"  Transcript saved to {transcript_path}")

    print(f"  {len(segments)} segments found")
    for seg in segments:
        print(f"    [{seg.id}] {format_duration(seg.start_ms)}-{format_duration(seg.end_ms)}  {seg.text[:60]}")

    # Plan
    plan = build_plan(segments, config)
    est_ms = estimate_duration_ms(plan, config.playback_speed)
    print(f"  Estimated output: {format_duration(est_ms)}")

    # Build
    print("Building practice audio ...")
    t0 = time.time()
    result = build_audio(audio, plan, config)
    elapsed = time.time() - t0
    print(f"  Built in {elapsed:.1f}s")

    # Export
    print(f"Exporting to {args.output} ...")
    export_mp3(result, args.output)
    print("Done.")


if __name__ == "__main__":
    main()
