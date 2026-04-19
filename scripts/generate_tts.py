"""Generate TTS audio files using Qwen3-TTS via MLX-Audio.

Supports three voice modes:
  - base: Voice cloning from a reference audio file (3-second minimum)
  - design: Generate voice from a text description (e.g., "female, British narrator")
  - custom: Use pre-defined CustomVoice speakers (Chelsie, Ethan, Vivienne, Ryan)

Usage:
  python scripts/generate_tts.py \
    --model-path models/Qwen3-TTS-12Hz-1.7B-Base-8bit \
    --mode base \
    --ref-audio voices/ref.wav \
    --ref-text "Reference text matching the audio." \
    --input-text "Text to synthesize." \
    --output output/movie/passage_01.mp3

  python scripts/generate_tts.py \
    --model-path models/Qwen3-TTS-12Hz-1.7B-VoiceDesign-8bit \
    --mode design \
    --speaker-design "female, warm and clear English narrator" \
    --input-text "Text to synthesize." \
    --output output/movie/passage_01.mp3

  python scripts/generate_tts.py \
    --model-path models/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit \
    --mode custom \
    --speaker-name Chelsie \
    --speaker-instruct "Read slowly and clearly for a listening exercise." \
    --input-text "Text to synthesize." \
    --output output/movie/passage_01.mp3
"""

import argparse
import json
import os
import sys
import time

SUPPORTED_MODES = ("base", "design", "custom")
CUSTOM_VOICES = ("Chelsie", "Ethan", "Vivienne", "Ryan")

# Trailing silence appended to every generated audio clip (seconds).
# Gives listeners a moment to process the sentence before the clip ends.
TRAILING_SILENCE_SECONDS = 1.0


def _append_trailing_silence(audio, sample_rate):
    """Concatenate `TRAILING_SILENCE_SECONDS` of zeros onto an mx audio array."""
    import mlx.core as mx

    silence_shape = list(audio.shape)
    silence_shape[0] = int(sample_rate * TRAILING_SILENCE_SECONDS)
    silence = mx.zeros(tuple(silence_shape), dtype=audio.dtype)
    return mx.concatenate([audio, silence], axis=0)


def check_mlx_audio():
    try:
        import mlx_audio

        return True
    except ImportError:
        return False


def generate_base(
    model, text, ref_audio, ref_text, output_path, sample_rate, verbose=False
):
    from mlx_audio.tts.generate import generate_audio

    results = generate_audio(
        model=model,
        text=text,
        lang_code="English",
        ref_audio=ref_audio,
        ref_text=ref_text,
        output_path=os.path.dirname(output_path) or ".",
        file_prefix=os.path.splitext(os.path.basename(output_path))[0],
        audio_format=os.path.splitext(output_path)[1].lstrip(".") or "mp3",
        join_audio=True,
        fix_mistral_regex=True,
        verbose=verbose,
    )
    _move_output(results, output_path)


def generate_design(
    model, text, speaker_design, output_path, sample_rate, verbose=False
):
    import mlx.core as mx
    from mlx_audio.audio_io import write as audio_write

    segments = [s.strip() for s in text.split("\n") if s.strip()]
    audio = []
    for i, seg in enumerate(segments):
        if verbose:
            print(f"  Segment {i + 1}/{len(segments)}: {seg[:60]}...")
        results = model.generate_voice_design(
            text=seg, instruct=speaker_design, verbose=verbose
        )
        for result in results:
            audio.append(result.audio)

    if audio:
        combined = _append_trailing_silence(mx.concatenate(audio, axis=0), sample_rate)
        audio_write(output_path, combined, sample_rate)


def generate_custom(
    model, text, speaker_name, speaker_instruct, output_path, sample_rate, verbose=False
):
    import mlx.core as mx
    from mlx_audio.audio_io import write as audio_write

    segments = [s.strip() for s in text.split("\n") if s.strip()]
    audio = []
    for i, seg in enumerate(segments):
        if verbose:
            print(f"  Segment {i + 1}/{len(segments)}: {seg[:60]}...")
        results = model.generate_custom_voice(
            text=seg, speaker=speaker_name, instruct=speaker_instruct, verbose=verbose
        )
        for result in results:
            audio.append(result.audio)

    if audio:
        combined = _append_trailing_silence(mx.concatenate(audio, axis=0), sample_rate)
        audio_write(output_path, combined, sample_rate)


def _move_output(results, output_path):
    if results and hasattr(results, "output_path"):
        actual = results.output_path
        if actual != output_path and os.path.exists(actual):
            os.replace(actual, output_path)


def load_model(model_path, mode, verbose=False):
    from mlx_audio.tts.utils import load_model

    if verbose:
        print(f"Loading model from {model_path}...")
    tic = time.perf_counter()
    model = load_model(model_path)
    toc = time.perf_counter()
    if verbose:
        print(f"Model loaded in {toc - tic:.1f}s")
    return model


def generate_passage(
    model,
    mode,
    text,
    output_path,
    sample_rate,
    ref_audio=None,
    ref_text=None,
    speaker_design=None,
    speaker_name=None,
    speaker_instruct=None,
    verbose=False,
):
    if mode == "base":
        generate_base(
            model, text, ref_audio, ref_text, output_path, sample_rate, verbose
        )
    elif mode == "design":
        generate_design(model, text, speaker_design, output_path, sample_rate, verbose)
    elif mode == "custom":
        generate_custom(
            model,
            text,
            speaker_name,
            speaker_instruct,
            output_path,
            sample_rate,
            verbose,
        )


def main():
    parser = argparse.ArgumentParser(
        description="Generate TTS audio using Qwen3-TTS via MLX-Audio"
    )
    parser.add_argument(
        "--model-path", required=True, help="Path to Qwen3-TTS MLX model directory"
    )
    parser.add_argument(
        "--mode", choices=SUPPORTED_MODES, required=True, help="Voice generation mode"
    )
    parser.add_argument("--input-text", help="Text to synthesize (inline string)")
    parser.add_argument(
        "--input-file", help="JSON file with passages: [{id, text, speaker?}]"
    )
    parser.add_argument("--output", help="Output audio path (single text mode)")
    parser.add_argument(
        "--output-dir", help="Output directory (batch mode from --input-file)"
    )
    parser.add_argument(
        "--ref-audio", help="Reference audio for base mode (voice cloning)"
    )
    parser.add_argument(
        "--ref-text", help="Reference text for base mode (matches ref_audio)"
    )
    parser.add_argument("--speaker-design", help="Voice description for design mode")
    parser.add_argument(
        "--speaker-name",
        choices=CUSTOM_VOICES,
        help="Pre-defined voice for custom mode",
    )
    parser.add_argument(
        "--speaker-instruct", default="", help="Style instruction for custom mode"
    )
    parser.add_argument("--verbose", action="store_true", help="Show progress details")
    args = parser.parse_args()

    if not check_mlx_audio():
        print(
            "ERROR: mlx_audio is not installed. Install with: pip install mlx_audio",
            file=sys.stderr,
        )
        sys.exit(1)

    model = load_model(args.model_path, args.mode, args.verbose)
    sample_rate = getattr(model, "sample_rate", 24000)

    if args.input_file:
        if not args.output_dir:
            parser.error("--output-dir is required when using --input-file")
        os.makedirs(args.output_dir, exist_ok=True)
        with open(args.input_file, "r", encoding="utf-8") as f:
            passages = json.load(f)

        voice_map = {}
        if args.mode == "custom":
            for p in passages:
                speaker = p.get("speaker", "Chelsie")
                if speaker not in voice_map:
                    voice_map[speaker] = {
                        "name": speaker,
                        "instruct": args.speaker_instruct or "Read slowly and clearly.",
                    }

        for p in passages:
            passage_id = p.get("id", "passage")
            text = p["text"]
            ext = ".mp3"
            out_path = os.path.join(args.output_dir, f"{passage_id}{ext}")
            if args.verbose:
                print(f"Generating {passage_id}...")

            kwargs = {}
            if args.mode == "base":
                kwargs = {"ref_audio": args.ref_audio, "ref_text": args.ref_text}
            elif args.mode == "design":
                speaker = p.get("speaker", "")
                desc = args.speaker_design or "female, warm and clear English narrator"
                if speaker and speaker.lower() in ("male", "man", "boy"):
                    desc = (
                        desc.replace("female", "male")
                        .replace("woman", "man")
                        .replace("girl", "boy")
                    )
                kwargs = {"speaker_design": desc}
            elif args.mode == "custom":
                speaker = p.get("speaker", "Chelsie")
                voice_info = voice_map.get(
                    speaker, {"name": "Chelsie", "instruct": args.speaker_instruct}
                )
                kwargs = {
                    "speaker_name": voice_info["name"],
                    "speaker_instruct": voice_info["instruct"],
                }

            generate_passage(
                model=model,
                mode=args.mode,
                text=text,
                output_path=out_path,
                sample_rate=sample_rate,
                verbose=args.verbose,
                **kwargs,
            )
            if args.verbose:
                print(f"  Saved: {out_path}")

    elif args.input_text:
        if not args.output:
            parser.error("--output is required when using --input-text")
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)

        kwargs = {}
        if args.mode == "base":
            if not args.ref_audio or not args.ref_text:
                parser.error("--ref-audio and --ref-text are required for base mode")
            kwargs = {"ref_audio": args.ref_audio, "ref_text": args.ref_text}
        elif args.mode == "design":
            kwargs = {
                "speaker_design": args.speaker_design
                or "female, warm and clear English narrator"
            }
        elif args.mode == "custom":
            kwargs = {
                "speaker_name": args.speaker_name or "Chelsie",
                "speaker_instruct": args.speaker_instruct
                or "Read slowly and clearly for a listening exercise.",
            }

        generate_passage(
            model=model,
            mode=args.mode,
            text=args.input_text,
            output_path=args.output,
            sample_rate=sample_rate,
            verbose=args.verbose,
            **kwargs,
        )
        if args.verbose:
            print(f"Saved: {args.output}")
    else:
        parser.error("Provide either --input-text or --input-file")


if __name__ == "__main__":
    main()
