# YouTube Downloader

A Python desktop application and command-line tool for downloading YouTube audio
and video to a local folder.

## Features

- Download audio and convert it to MP3
- Download video and audio, then combine them into an AVI or MP4 file
- Choose video quality: 360p, 480p, 720p, 1080p, or the best available
- Process multiple YouTube URLs in one run
- Use the graphical interface or command line
- Skip existing files by default, or choose to overwrite them
- View download progress and activity in the GUI
- Write activity logs to `downloader.log` in the output folder

## Requirements

- Python 3.x
- [ffmpeg](https://ffmpeg.org/) installed and available on your `PATH`
- The `pytubefix` Python package
- Tkinter for the desktop GUI (usually included with Python)

Install `pytubefix`: 

```bash
python -m pip install pytubefix
```

If `python` is not recognized in Windows PowerShell, use the Python Launcher:

```powershell
py -m pip install pytubefix
```

Check that ffmpeg is available by running `ffmpeg -version` in a terminal.

## Graphical interface

From the project folder, launch the app:

```bash
python gui.py
```

On Windows, you can also run:

```powershell
py .\gui.py
```

Paste one or more URLs into the **Video Links** box, then choose a format,
video quality, and save folder. Click **Start download** to begin. Progress and
activity are shown in the window.

The download mode options are:

- **MP3 audio** — download audio and convert it to MP3
- **Video** — download video and audio, then combine them into the selected video format
- **Both** — create an MP3 and a video file

Select **AVI** or **MP4** as the video format; AVI is the default. The quality
setting applies to video downloads. The default output folder is
`D:/Lagu`. You can browse to another folder in the app. Downloads skip files
that already exist unless **Replace files that already exist** is selected.

## Command line

Run the interactive terminal version:

```bash
python yt.py
```

In interactive mode, paste one or more URLs, choose a download mode, and select
a video quality and (for video downloads) a video format.

For a direct CLI run, specify the mode and at least one URL:

```bash
python yt.py --mode mp3 --quality 480 --urls "https://youtu.be/abc123"
python yt.py --mode avi --video-format mp4 --quality 720 --output-dir "D:/Lagu" --urls "https://youtu.be/abc123"
python yt.py --mode both --quality 1080 --urls "https://youtu.be/abc123" --overwrite
```

Available options:

- `--mode`: `mp3`, `avi`, or `both`
- `--video-format`: `avi` or `mp4` (default: `avi`; applies to `avi` and `both` modes)
- `--quality`: `360`, `480`, `720`, `1080`, or `best` (default: `480`)
- `--output-dir`: output folder (default: `D:/Lagu`)
- `--overwrite`: replace files that already exist
- `--urls`: one or more YouTube URLs
- `--log-file`: log file path (default: `<output-dir>/downloader.log`)

Example with a custom log location:

```bash
python yt.py --mode avi --quality 720 --urls "https://youtu.be/abc123" --log-file "D:/Logs/youtube.log"
```

## Logs and troubleshooting

The application writes activity to `downloader.log` in the output folder. The
log includes processed URLs, titles, download progress, skipped files, and
conversion results or errors.

If pytubefix reports that a request was detected as a bot, upgrade it:

```bash
python -m pip install --upgrade pytubefix
```

YouTube may still reject requests depending on the network address or session,
so successful access is not guaranteed. See the
[pytubefix PO token guide](https://pytubefix.readthedocs.io/en/latest/user/po_token.html)
for more information.

## Notes

- Output filenames are cleaned to make them safer for common filesystems.
- Video quality may fall back to the highest available stream if the requested
  resolution is not available.
- ffmpeg is used to convert audio to MP3 and combine video and audio into AVI or MP4.

## License

This project is open source and may be modified.
