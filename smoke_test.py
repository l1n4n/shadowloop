#!/usr/bin/env python3
"""
Smoke test for ShadowLoop pipeline.
Tests the full end-to-end workflow with the pitch.mp3 file.
"""

import os
import sys

# Test 1: Check ffmpeg
print("=" * 60)
print("SMOKE TEST: ShadowLoop Pipeline")
print("=" * 60)

try:
    from shadowloop.ingest import check_ffmpeg, load_audio, prepare_for_transcription, export_temp_wav
    from shadowloop.segmenter import segment_audio, merge_segments, delete_segment
    from shadowloop.planner import build_plan
    from shadowloop.builder import build_audio
    from shadowloop.exporters import export_mp3
    from shadowloop.config import ShadowingConfig
    print("\n[1/11] Import modules: PASS")
except Exception as e:
    print(f"\n[1/11] Import modules: FAIL: {e}")
    sys.exit(1)

try:
    check_ffmpeg()
    print("[2/11] Check ffmpeg: PASS")
except Exception as e:
    print(f"[2/11] Check ffmpeg: FAIL: {e}")
    sys.exit(1)

# Test 2: Load audio
audio_file = "/home/idlab288/PycharmProjects/shadowing_app/pitch.mp3"
try:
    audio = load_audio(audio_file)
    audio_duration_ms = len(audio)
    audio_duration_sec = audio_duration_ms / 1000.0
    print(f"[3/11] Load audio: PASS (duration: {audio_duration_sec:.2f}s)")
except Exception as e:
    print(f"[3/11] Load audio: FAIL: {e}")
    sys.exit(1)

# Test 3: Prepare for transcription
try:
    prepared_audio = prepare_for_transcription(audio)
    print("[4/11] Prepare for transcription: PASS")
except Exception as e:
    print(f"[4/11] Prepare for transcription: FAIL: {e}")
    sys.exit(1)

# Test 4: Export temp WAV
temp_wav_path = None
try:
    temp_wav_path = export_temp_wav(prepared_audio)
    print(f"[5/11] Export temp WAV: PASS (path: {temp_wav_path})")
except Exception as e:
    print(f"[5/11] Export temp WAV: FAIL: {e}")
    sys.exit(1)

# Test 5: Segment audio
segments = None
try:
    segments = segment_audio(temp_wav_path, audio_duration_ms, model_size="base")
    print(f"[6/11] Segment audio: PASS ({len(segments)} segments)")
    for seg in segments:
        duration_ms = seg.duration_ms
        print(f"       - Segment {seg.id}: '{seg.text[:50]}...' ({seg.start_ms}ms-{seg.end_ms}ms, {duration_ms}ms)")
except Exception as e:
    print(f"[6/11] Segment audio: FAIL: {e}")
    if temp_wav_path and os.path.exists(temp_wav_path):
        os.remove(temp_wav_path)
    sys.exit(1)

# Clean up temp WAV file
if temp_wav_path and os.path.exists(temp_wav_path):
    try:
        os.remove(temp_wav_path)
        print("[7/11] Clean up temp WAV: PASS")
    except Exception as e:
        print(f"[7/11] Clean up temp WAV: FAIL: {e}")
else:
    print("[7/11] Clean up temp WAV: PASS (file already removed)")

# Test 6: Merge segments (if we have at least 2)
try:
    if len(segments) >= 2:
        merged_segments = merge_segments(segments, 0, 1)
        print(f"[8/11] Merge segments 0+1: PASS ({len(merged_segments)} segments after merge)")
        print(f"       - Merged segment: '{merged_segments[0].text[:50]}...'")
    else:
        print(f"[8/11] Merge segments 0+1: SKIP (only {len(segments)} segment(s))")
except Exception as e:
    print(f"[8/11] Merge segments 0+1: FAIL: {e}")
    sys.exit(1)

# Test 7: Delete segment (on original segments, not merged)
try:
    if len(segments) > 0:
        last_id = segments[-1].id
        deleted_segments = delete_segment(segments, last_id)
        print(f"[9/11] Delete last segment: PASS ({len(deleted_segments)} segments after delete)")
    else:
        print(f"[9/11] Delete last segment: SKIP (no segments)")
except Exception as e:
    print(f"[9/11] Delete last segment: FAIL: {e}")
    sys.exit(1)

# Test 8: Build plan and audio (using ORIGINAL segments, not edited ones)
try:
    config = ShadowingConfig(
        repeat_count=2,
        pause_between_repeats_ms=1500,
        pause_between_sentences_ms=3000,
        playback_speed=1.0
    )
    plan = build_plan(segments, config)
    print(f"[10/11] Build plan: PASS ({len(plan)} actions)")

    output_audio = build_audio(audio, plan, config)
    output_duration_ms = len(output_audio)
    output_duration_sec = output_duration_ms / 1000.0
    print(f"        Output audio duration: {output_duration_sec:.2f}s")
except Exception as e:
    print(f"[10/11] Build plan and audio: FAIL: {e}")
    sys.exit(1)

# Test 9: Export to MP3
output_path = "/tmp/shadowloop_smoke_test.mp3"
try:
    export_mp3(output_audio, output_path, bitrate="192k")

    # Get file size
    file_size_bytes = os.path.getsize(output_path)
    file_size_mb = file_size_bytes / (1024 * 1024)

    # Verify the file exists and has content
    if os.path.exists(output_path) and file_size_bytes > 0:
        print(f"[11/11] Export MP3: PASS")
        print(f"        Output file: {output_path}")
        print(f"        File size: {file_size_mb:.2f} MB ({file_size_bytes} bytes)")
        print(f"        Duration: {output_duration_sec:.2f}s")
    else:
        print(f"[11/11] Export MP3: FAIL (file is empty or missing)")
        sys.exit(1)
except Exception as e:
    print(f"[11/11] Export MP3: FAIL: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("SMOKE TEST COMPLETE: ALL STEPS PASSED")
print("=" * 60)
