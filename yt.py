#!/usr/bin/env python3
"""YouTube Downloader CLI and interactive utility.

Examples:
    python yt.py --mode mp3 --quality 480 --urls "https://youtu.be/..." "https://youtu.be/..."
    python yt.py --mode both --quality 720 --output-dir "D:/Lagu" --overwrite
    python yt.py
"""

import argparse
import logging
import re
import subprocess
import sys
from pathlib import Path

try:
    import audioop
except ImportError:
    try:
        import audioop_lts

        sys.modules["audioop"] = audioop_lts
        sys.modules["pyaudioop"] = audioop_lts
    except ImportError:
        pass

from pytubefix import YouTube

DEFAULT_OUTPUT_DIR = Path("D:/Lagu")
SUPPORTED_RESOLUTIONS = {"360": "360p", "480": "480p", "720": "720p", "1080": "1080p"}
LOGGER = logging.getLogger("yt_downloader")
_progress_log_threshold: dict[int, int] = {}


def setup_logging(log_file: Path) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))

    LOGGER.setLevel(logging.INFO)
    LOGGER.handlers.clear()
    LOGGER.addHandler(handler)
    LOGGER.propagate = False
    LOGGER.info("Logging started. Log file: %s", log_file)


def normalize_quality(value: str | None) -> str:
    if not value:
        return "480p"

    normalized = str(value).strip().lower().replace("p", "")
    if normalized in SUPPORTED_RESOLUTIONS:
        return SUPPORTED_RESOLUTIONS[normalized]
    if normalized in {"best", "max"}:
        return "best"
    raise argparse.ArgumentTypeError(
        f"Invalid quality '{value}'. Choose one of: 360, 480, 720, 1080, best."
    )


def ensure_output_dir(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {directory}")


def show_menu() -> str:
    print("\n" + "=" * 35)
    print("      YouTube Downloader")
    print("=" * 35)
    print("  [1] Download MP3 (Audio only)")
    print("  [2] Download AVI (Video + Audio)")
    print("  [3] Download Both")
    print("=" * 35)

    while True:
        choice = input("Select an option: ").strip()
        if choice in {"1", "2", "3"}:
            return choice
        print("Invalid choice. Please enter 1, 2, or 3.")


def prompt_for_quality() -> str:
    print("\nAvailable video qualities: 360, 480, 720, 1080, best")
    while True:
        value = input("Select video quality: ").strip().lower()
        try:
            return normalize_quality(value)
        except argparse.ArgumentTypeError as exc:
            print(f"  -> {exc}")


def get_urls() -> list[str]:
    print("\nEnter YouTube URLs (you can paste them concatenated together).\n")
    raw_input = input("  URLs: ").strip()
    if not raw_input:
        return []

    spaced_input = raw_input.replace("https", " https")
    found_links = re.findall(r"(https?://[^\s]+)", spaced_input)
    urls: list[str] = []

    for link in found_links:
        clean_link = link.strip().rstrip(")")
        if clean_link.endswith("http"):
            clean_link = clean_link[:-4]
        if clean_link.endswith("https"):
            clean_link = clean_link[:-5]
        if clean_link and clean_link not in urls:
            urls.append(clean_link)

    print(f"  Detected {len(urls)} URL(s)")
    return urls


def on_progress(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    if not total_size:
        return

    bytes_downloaded = total_size - bytes_remaining
    percentage = (bytes_downloaded / total_size) * 100
    print(f"\r  -> Progress: {percentage:.1f}%", end="", flush=True)

    progress_step = min(100, int(percentage // 10) * 10)
    stream_id = id(stream)
    if progress_step >= 10 and progress_step > _progress_log_threshold.get(stream_id, 0):
        LOGGER.info(
            "Download progress: %s%% (%s)",
            progress_step,
            getattr(stream, "resolution", getattr(stream, "mime_type", "stream")),
        )
        _progress_log_threshold[stream_id] = progress_step
    if bytes_remaining <= 0:
        print()


def clean_filename(title: str, index: int) -> str:
    ascii_name = title.encode("ascii", "ignore").decode("ascii")
    safe_name = "".join(c for c in ascii_name if c.isalnum() or c in (" ", "-", "_")).strip()
    if not safe_name:
        safe_name = f"Video_{index}"
    return safe_name[:40]


def remove_temp_file(path: str | Path) -> None:
    temp = Path(path)
    if temp.exists():
        temp.unlink()


def convert_to_mp3(
    input_file: str | Path,
    output_dir: Path,
    safe_name: str,
    overwrite: bool = False,
) -> None:
    output_file = output_dir / f"{safe_name}.mp3"
    if output_file.exists() and not overwrite:
        print(f"  -> Skip: '{output_file.name}' already exists. Use --overwrite to replace it.")
        LOGGER.info("Skipped existing file: %s", output_file)
        remove_temp_file(input_file)
        return

    if output_file.exists() and overwrite:
        output_file.unlink()

    command = ["ffmpeg", "-y", "-i", str(input_file), "-q:a", "0", "-map", "a", str(output_file)]

    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"\n  -> Converted to: '{output_file}'")
        LOGGER.info("MP3 conversion completed: %s", output_file)
        remove_temp_file(input_file)
    except Exception as exc:
        print(f"\n  Error converting to MP3: {exc}")
        LOGGER.exception("MP3 conversion failed for %s", output_file)
        remove_temp_file(input_file)


def download_mp3(yt: YouTube, output_dir: Path, safe_name: str, overwrite: bool = False) -> None:
    audio_stream = yt.streams.get_audio_only()
    if not audio_stream:
        print("  -> Error: No audio stream available.")
        return

    expected_filename = f"{safe_name}.mp3"
    target_path = output_dir / expected_filename
    if target_path.exists() and not overwrite:
        print(f"  -> Skip: '{expected_filename}' already exists. Use --overwrite to replace it.")
        LOGGER.info("Skipped existing file: %s", target_path)
        return

    print("  -> Downloading audio...")
    LOGGER.info("Audio download started: %s", yt.title)
    _progress_log_threshold.pop(id(audio_stream), None)
    file_path = audio_stream.download(output_path=str(output_dir))
    convert_to_mp3(file_path, output_dir, safe_name, overwrite=overwrite)


def resolve_video_stream(yt: YouTube, quality: str):
    if quality == "best":
        stream = yt.streams.filter(only_video=True).order_by("resolution").desc().first()
        if stream:
            print(f"  -> Selected highest available video quality: {stream.resolution}")
        return stream

    stream = yt.streams.filter(res=quality, only_video=True).first()
    if stream:
        return stream

    stream = yt.streams.filter(only_video=True).order_by("resolution").desc().first()
    if stream:
        print(f"  -> Requested quality '{quality}' not found. Using fallback: {stream.resolution}")
    return stream


def download_avi(
    yt: YouTube,
    output_dir: Path,
    safe_name: str,
    quality: str = "480p",
    overwrite: bool = False,
) -> None:
    video_stream = resolve_video_stream(yt, quality)
    audio_stream = yt.streams.get_audio_only()

    if not video_stream or not audio_stream:
        print("  -> Error: Could not find valid streams.")
        return

    expected_filename = f"{safe_name}.avi"
    final_path = output_dir / expected_filename
    if final_path.exists() and not overwrite:
        print(f"  -> Skip: '{expected_filename}' already exists. Use --overwrite to replace it.")
        LOGGER.info("Skipped existing file: %s", final_path)
        return

    if final_path.exists() and overwrite:
        final_path.unlink()

    print(f"  -> Downloading video stream ({video_stream.resolution})...")
    LOGGER.info("Video download started: %s (%s)", yt.title, video_stream.resolution)
    _progress_log_threshold.pop(id(video_stream), None)
    video_path = video_stream.download(output_path=str(output_dir), filename="temp_vid.mp4")
    print("\n  -> Downloading audio stream...")
    LOGGER.info("Audio download started for video: %s", yt.title)
    _progress_log_threshold.pop(id(audio_stream), None)
    audio_path = audio_stream.download(output_path=str(output_dir), filename="temp_aud.m4a")
    print("\n  -> Merging and converting to AVI...")

    width, height = (854, 480) if "480" in str(video_stream.resolution) else (1280, 720) if "720" in str(video_stream.resolution) else (1920, 1080)
    filter_expr = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,fps=30"
    )

    command = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-i",
        audio_path,
        "-c:v",
        "mpeg4",
        "-vtag",
        "xvid",
        "-q:v",
        "3",
        "-vf",
        filter_expr,
        "-c:a",
        "libmp3lame",
        "-ar",
        "44100",
        "-ac",
        "2",
        "-b:a",
        "128k",
        str(final_path),
    ]

    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"  -> Saved to: '{final_path}'")
        LOGGER.info("AVI conversion completed: %s", final_path)
        remove_temp_file(video_path)
        remove_temp_file(audio_path)
    except Exception as exc:
        print(f"  -> Error merging: {exc}")
        LOGGER.exception("AVI conversion failed for %s", final_path)
        remove_temp_file(video_path)
        remove_temp_file(audio_path)


def process_url(url: str, download_type: str, output_dir: Path, quality: str, index: int, overwrite: bool) -> None:
    print(f"  Processing: {url}")
    LOGGER.info("Processing URL: %s", url)
    yt = YouTube(url, on_progress_callback=on_progress)
    print(f"  Title: {yt.title}")
    LOGGER.info("Resolved video title: %s", yt.title)

    safe_name = clean_filename(yt.title, index)

    if download_type == "1":
        download_mp3(yt, output_dir, safe_name, overwrite=overwrite)
    elif download_type == "2":
        download_avi(yt, output_dir, safe_name, quality=quality, overwrite=overwrite)
    elif download_type == "3":
        download_mp3(yt, output_dir, safe_name, overwrite=overwrite)
        download_avi(yt, output_dir, safe_name, quality=quality, overwrite=overwrite)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download YouTube audio/video files using pytubefix.")
    parser.add_argument("--mode", choices=["mp3", "avi", "both"], default=None, help="Download mode")
    parser.add_argument("--quality", default="480", help="Video quality: 360, 480, 720, 1080, best")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Folder where files are saved")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    parser.add_argument("--urls", nargs="+", default=[], help="One or more YouTube URLs")
    parser.add_argument(
        "--log-file",
        type=Path,
        default=None,
        help="Path for the activity log (default: <output-dir>/downloader.log)",
    )
    return parser.parse_args()


def run_interactive(output_dir: Path) -> None:
    while True:
        urls = get_urls()
        if not urls:
            print("No URLs detected. Try again.")
            continue

        choice = show_menu()
        quality = prompt_for_quality()
        print(f"\nStarting download for {len(urls)} video(s)...\n")

        for index, url in enumerate(urls, start=1):
            try:
                print(f"[{index}/{len(urls)}]", end=" ")
                process_url(url, choice, output_dir, quality, index, overwrite=False)
            except Exception as exc:
                print(f"  Error processing {url}: {exc}")
                LOGGER.exception("Failed to process URL: %s", url)

        print("\nAll downloads complete!")
        again = input("\nDownload more videos? (y/n): ").strip().lower()
        if again != "y":
            print("Goodbye!")
            break


def run_cli(args: argparse.Namespace) -> int:
    output_dir = args.output_dir
    ensure_output_dir(output_dir)
    log_file = args.log_file or output_dir / "downloader.log"
    setup_logging(log_file)

    urls = args.urls
    if not urls:
        print("No URLs supplied. Use --urls or run without CLI options to use interactive mode.")
        return 1

    mode = args.mode
    quality = normalize_quality(args.quality)

    if mode is None:
        mode = "mp3"

    if mode == "mp3":
        mode_value = "1"
    elif mode == "avi":
        mode_value = "2"
    else:
        mode_value = "3"

    print(f"\nStarting {mode} download for {len(urls)} URL(s)...")
    for index, url in enumerate(urls, start=1):
        try:
            print(f"[{index}/{len(urls)}]", end=" ")
            process_url(url, mode_value, output_dir, quality, index, overwrite=args.overwrite)
        except Exception as exc:
            print(f"  Error processing {url}: {exc}")
            LOGGER.exception("Failed to process URL: %s", url)

    print("\nAll downloads complete!")
    LOGGER.info("Download run completed.")
    return 0


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir

    if not args.urls:
        ensure_output_dir(output_dir)
        log_file = args.log_file or output_dir / "downloader.log"
        setup_logging(log_file)
        run_interactive(output_dir)
        return 0

    return run_cli(args)


if __name__ == "__main__":
    raise SystemExit(main())