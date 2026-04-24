"""ShadowLoop - Gradio UI for shadowing practice."""

import os
import tempfile
from typing import List

import gradio as gr

from shadowloop.config import Segment, ShadowingConfig, segments_from_dicts
from shadowloop.ingest import check_ffmpeg, load_audio, prepare_for_transcription, export_temp_wav
from shadowloop.segmenter import segment_audio, merge_segments, split_segment, delete_segment, segments_from_transcript
from shadowloop.planner import build_plan, estimate_duration_ms
from shadowloop.builder import build_audio
from shadowloop.exporters import export_mp3


CUSTOM_CSS = """
/* Tight section spacing */
.phase-section { padding: 8px 12px !important; margin-bottom: 4px !important; border-radius: 6px; }

/* Section titles — via elem_id */
#title-upload h3 { font-size: 20px !important; font-weight: 600; color: #5b5ea6 !important; margin: 0 !important; }
#title-review h3 { font-size: 20px !important; font-weight: 600; color: #9a7b4f !important; margin: 0 !important; }
#title-build  h3 { font-size: 20px !important; font-weight: 600; color: #4a8c72 !important; margin: 0 !important; }

/* Description text — same color as titles, via elem_id */
#desc-upload p { font-size: 15px !important; font-weight: 400; color: #5b5ea6 !important; margin: 0 0 4px 0 !important; padding: 0 !important; }
#desc-review p { font-size: 15px !important; font-weight: 400; color: #9a7b4f !important; margin: 0 0 4px 0 !important; padding: 0 !important; }
#desc-build  p { font-size: 15px !important; font-weight: 400; color: #4a8c72 !important; margin: 0 0 4px 0 !important; padding: 0 !important; }

/* Intro — compact */
#intro-text h1 { font-size: 26px !important; margin-bottom: 0 !important; }
#intro-text p { font-size: 18px !important; color: #78716c !important; margin: 0 !important; padding: 0 !important; }

/* Color-coded How it works steps */
.step-upload { color: #5b5ea6; font-weight: 600; }
.step-review { color: #9a7b4f; font-weight: 600; }
.step-build  { color: #4a8c72; font-weight: 600; }

/* Remove group borders/padding that Gradio adds */
.phase-section > .panel { padding: 0 !important; border: none !important; }
"""


def generate_transcript_file(segments: List[Segment]) -> str | None:
    """Write segments to a temp .txt file for download."""
    if not segments:
        return None
    path = os.path.join(tempfile.gettempdir(), "shadowloop_transcript.txt")
    with open(path, "w", encoding="utf-8") as f:
        for seg in segments:
            f.write(f"[{seg.start_ms / 1000:.1f}s - {seg.end_ms / 1000:.1f}s] {seg.text}\n")
    return path


def segments_to_html(segments: List[Segment]) -> str:
    """Render segments as an HTML table."""
    if not segments:
        return "<p>No segments yet.</p>"
    rows = ""
    for seg in segments:
        start_s = seg.start_ms / 1000
        end_s = seg.end_ms / 1000
        dur_s = seg.duration_ms / 1000
        rows += (
            f"<tr><td>{seg.id}</td><td>{seg.text}</td>"
            f"<td>{start_s:.1f}s</td><td>{end_s:.1f}s</td><td>{dur_s:.1f}s</td></tr>"
        )
    return (
        '<table style="width:100%;border-collapse:collapse;font-size:16px;">'
        '<tr style="background:#f0f0f0;"><th>ID</th><th>Text</th>'
        "<th>Start</th><th>End</th><th>Duration</th></tr>"
        f"{rows}</table>"
    )


def on_transcribe(audio_file):
    """Transcribe audio file and segment into sentences."""
    if audio_file is None:
        return None, None, "<p>Please upload an audio file.</p>", "Please upload an audio file.", None
    try:
        audio = load_audio(audio_file)
        asr_audio = prepare_for_transcription(audio)
        wav_path = export_temp_wav(asr_audio)
        try:
            segments = segment_audio(wav_path, len(audio))
        finally:
            os.unlink(wav_path)
        if not segments:
            return audio, None, "<p>No speech detected.</p>", "No speech detected in the audio.", None
        html = segments_to_html(segments)
        transcript_path = generate_transcript_file(segments)
        return audio, segments, html, f"Found {len(segments)} sentences. Review and edit below.", transcript_path
    except Exception as e:
        return None, None, f"<p>Error: {e}</p>", f"Error: {e}", None


def on_upload_transcript(audio_state, transcript_file):
    """Load segments from uploaded transcript file."""
    if audio_state is None:
        return None, None, "<p>Please upload audio first.</p>", "Please upload audio first.", None
    if transcript_file is None:
        return None, None, "<p>Please upload a transcript file.</p>", "Please upload a transcript file.", None
    try:
        with open(transcript_file, "r", encoding="utf-8") as f:
            text = f.read()

        audio = load_audio(audio_state)
        audio_duration_ms = len(audio)

        segments = segments_from_transcript(text, audio_duration_ms)
        if not segments:
            return None, None, "<p>No text found in transcript.</p>", "No text found in transcript.", None

        html = segments_to_html(segments)
        transcript_path = generate_transcript_file(segments)
        return audio, segments, html, f"Loaded {len(segments)} segments from transcript.", transcript_path
    except Exception as e:
        return None, None, f"<p>Error: {e}</p>", f"Error: {e}", None


def on_merge(segments_state, selected_ids_text):
    """Merge two adjacent segments."""
    segments = segments_from_dicts(segments_state) if segments_state else []
    if not segments:
        return segments_state, "<p>No segments loaded.</p>", "No segments loaded."
    try:
        ids = [int(x.strip()) for x in selected_ids_text.split(",")]
        if len(ids) != 2:
            return segments_state, segments_to_html(segments), "Select exactly 2 adjacent segment IDs (e.g. '0,1')."
        new_segments = merge_segments(segments, ids[0], ids[1])
        return new_segments, segments_to_html(new_segments), f"Merged segments {ids[0]} and {ids[1]}."
    except Exception as e:
        return segments_state, segments_to_html(segments), f"Merge error: {e}"


def on_split(segments_state, segment_id, split_time_s):
    """Split a segment at the specified time offset."""
    segments = segments_from_dicts(segments_state) if segments_state else []
    if not segments:
        return segments_state, "<p>No segments loaded.</p>", "No segments loaded."
    try:
        seg_id = int(segment_id)
        offset_ms = int(float(split_time_s) * 1000)
        new_segments = split_segment(segments, seg_id, offset_ms)
        return new_segments, segments_to_html(new_segments), f"Split segment {seg_id} at {split_time_s}s."
    except Exception as e:
        return segments_state, segments_to_html(segments), f"Split error: {e}"


def on_delete(segments_state, segment_id):
    """Delete a segment."""
    segments = segments_from_dicts(segments_state) if segments_state else []
    if not segments:
        return segments_state, "<p>No segments loaded.</p>", "No segments loaded."
    try:
        seg_id = int(segment_id)
        new_segments = delete_segment(segments, seg_id)
        return new_segments, segments_to_html(new_segments), f"Deleted segment {seg_id}."
    except Exception as e:
        return segments_state, segments_to_html(segments), f"Delete error: {e}"


def on_estimate(segments_state, repeat_count, pause_repeats, pause_sentences, speed):
    """Estimate output duration."""
    segments = segments_from_dicts(segments_state) if segments_state else []
    if not segments:
        return "No segments loaded."
    config = ShadowingConfig(
        repeat_count=int(repeat_count),
        pause_between_repeats_ms=int(float(pause_repeats) * 1000),
        pause_between_sentences_ms=int(float(pause_sentences) * 1000),
        playback_speed=float(speed),
    )
    plan = build_plan(segments, config)
    total_ms = estimate_duration_ms(plan, config.playback_speed)
    minutes = total_ms // 60000
    seconds = (total_ms % 60000) // 1000
    return f"Estimated output: {minutes}m {seconds}s ({len(segments)} sentences x {config.repeat_count} repeats)"


def on_build(audio_state, segments_state, repeat_count, pause_repeats, pause_sentences, speed):
    """Build the practice audio file."""
    segments = segments_from_dicts(segments_state) if segments_state else []
    if audio_state is None or not segments:
        return None, None, "Upload and transcribe audio first."
    config = ShadowingConfig(
        repeat_count=int(repeat_count),
        pause_between_repeats_ms=int(float(pause_repeats) * 1000),
        pause_between_sentences_ms=int(float(pause_sentences) * 1000),
        playback_speed=float(speed),
    )
    errors = config.validate()
    if errors:
        return None, None, "Config errors: " + "; ".join(errors)
    try:
        plan = build_plan(segments, config)
        result_audio = build_audio(audio_state, plan, config)
        output_path = os.path.join(tempfile.gettempdir(), "shadowloop_output.mp3")
        export_mp3(result_audio, output_path)
        total_ms = len(result_audio)
        minutes = total_ms // 60000
        seconds = (total_ms % 60000) // 1000
        return output_path, output_path, f"Built practice audio: {minutes}m {seconds}s"
    except Exception as e:
        return None, None, f"Build error: {e}"


def create_app():
    """Create and return the Gradio app."""
    with gr.Blocks(title="ShadowLoop") as app:
        gr.Markdown(
            "# ShadowLoop\n"
            "Turn any audio into a shadowing practice loop.\n\n"
            '**How it works:** <span class="step-upload">Upload audio + transcribe</span> → '
            '<span class="step-review">review the detected sentences</span> → '
            '<span class="step-build">build a practice file</span> that repeats each sentence with pauses.',
            elem_id="intro-text",
        )

        audio_state = gr.State(value=None)
        segments_state = gr.State(value=None)

        # Phase 1: Upload
        with gr.Group(elem_classes=["phase-upload", "phase-section"]):
            gr.Markdown("### 1. Upload Audio", elem_id="title-upload")
            gr.Markdown("Upload audio and transcribe, or provide your own transcript.", elem_id="desc-upload")
            with gr.Row():
                with gr.Column(scale=3):
                    audio_input = gr.Audio(label="Audio file", type="filepath")
                    transcribe_btn = gr.Button("Transcribe", variant="primary")
                with gr.Column(scale=2):
                    transcript_input = gr.File(label="Upload transcript (.txt)", file_types=[".txt"])
                    transcript_btn = gr.Button("Use Transcript")
            status_text = gr.Textbox(label="Status", interactive=False)

        # Phase 2: Review
        with gr.Group(elem_classes=["phase-review", "phase-section"]):
            gr.Markdown("### 2. Review Sentences", elem_id="title-review")
            gr.Markdown("Check detected sentences. Expand 'Edit Segments' to merge, split, or delete.", elem_id="desc-review")
            segments_html = gr.HTML(value="<p>No segments yet.</p>")
            transcript_download = gr.File(label="Download Transcript", interactive=False, elem_classes=["compact-file"])
            with gr.Accordion("Edit Segments", open=False):
                with gr.Row():
                    with gr.Column():
                        merge_ids = gr.Textbox(label="Merge IDs (e.g. '0,1')", placeholder="0,1")
                        merge_btn = gr.Button("Merge")
                    with gr.Column():
                        split_id = gr.Number(label="Split segment ID", precision=0)
                        split_time = gr.Number(label="Split at (seconds from segment start)")
                        split_btn = gr.Button("Split")
                    with gr.Column():
                        delete_id = gr.Number(label="Delete segment ID", precision=0)
                        delete_btn = gr.Button("Delete")

        # Phase 3: Build
        with gr.Group(elem_classes=["phase-build", "phase-section"]):
            gr.Markdown("### 3. Configure & Build", elem_id="title-build")
            gr.Markdown("Set repeats and pauses, then build your practice audio.", elem_id="desc-build")
            with gr.Row():
                repeat_count = gr.Slider(1, 20, value=3, step=1, label="Repeat count")
                pause_repeats = gr.Slider(0, 10, value=2.5, step=0.5, label="Pause between repeats (s)")
                pause_sentences = gr.Slider(1, 15, value=4, step=0.5, label="Pause between sentences (s)")
                speed = gr.Slider(0.5, 2.0, value=1.0, step=0.01, label="Playback speed")
            with gr.Row():
                estimate_btn = gr.Button("Estimate Duration")
                estimate_text = gr.Textbox(label="Estimate", interactive=False)
            build_btn = gr.Button("Build Practice Audio", variant="primary")
            build_status = gr.Textbox(label="Build Status", interactive=False)
            with gr.Row(equal_height=True):
                output_audio = gr.Audio(label="Preview", type="filepath")
                download_file = gr.File(label="Download MP3")

        # Wire callbacks (KEEP EXACTLY AS-IS)
        transcribe_btn.click(
            on_transcribe,
            inputs=[audio_input],
            outputs=[audio_state, segments_state, segments_html, status_text, transcript_download],
        )
        transcript_btn.click(
            on_upload_transcript,
            inputs=[audio_input, transcript_input],
            outputs=[audio_state, segments_state, segments_html, status_text, transcript_download],
        )
        merge_btn.click(
            on_merge,
            inputs=[segments_state, merge_ids],
            outputs=[segments_state, segments_html, status_text],
        )
        split_btn.click(
            on_split,
            inputs=[segments_state, split_id, split_time],
            outputs=[segments_state, segments_html, status_text],
        )
        delete_btn.click(
            on_delete,
            inputs=[segments_state, delete_id],
            outputs=[segments_state, segments_html, status_text],
        )
        estimate_btn.click(
            on_estimate,
            inputs=[segments_state, repeat_count, pause_repeats, pause_sentences, speed],
            outputs=[estimate_text],
        )
        build_btn.click(
            on_build,
            inputs=[audio_state, segments_state, repeat_count, pause_repeats, pause_sentences, speed],
            outputs=[output_audio, download_file, build_status],
        )

    return app


if __name__ == "__main__":
    check_ffmpeg()
    app = create_app()
    theme = gr.themes.Soft(
        primary_hue=gr.themes.colors.stone,
        secondary_hue=gr.themes.colors.stone,
        neutral_hue=gr.themes.colors.stone,
        font=gr.themes.GoogleFont("Inter"),
    ).set(
        slider_color="#78716c",
        color_accent="#78716c",
        color_accent_soft="#e7e5e4",
        button_primary_background_fill="#57534e",
        button_primary_background_fill_hover="#44403c",
        button_primary_text_color="white",
        block_border_width="0px",
    )
    app.launch(server_name="0.0.0.0", theme=theme, css=CUSTOM_CSS)
