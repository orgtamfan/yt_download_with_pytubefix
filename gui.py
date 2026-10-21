#!/usr/bin/env python3
"""Tkinter desktop interface for the YouTube downloader."""

import argparse
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from yt import (
    DEFAULT_OUTPUT_DIR,
    LOGGER,
    ensure_output_dir,
    extract_urls,
    normalize_quality,
    process_url,
    setup_logging,
)


class DownloaderApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("720x760")
        self.root.minsize(620, 680)
        self.colors = {
            "background": "#f4f6f8",
            "surface": "#ffffff",
            "text": "#202124",
            "muted": "#687078",
            "accent": "#d93025",
            "accent_active": "#b9251d",
            "border": "#e2e6ea",
        }
        self.events: queue.Queue[tuple[str, str | float]] = queue.Queue()

        root.configure(background=self.colors["background"])
        self._configure_styles()

        content = ttk.Frame(root, padding=(28, 24), style="App.TFrame")
        content.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        content.columnconfigure(0, weight=1)
        content.rowconfigure(3, weight=1)
        content.rowconfigure(5, weight=1)

        ttk.Label(content, text="Video Downloader", style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            content,
            text="Save videos and audio to your computer",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(3, 20))

        urls_card = ttk.Frame(content, padding=16, style="Card.TFrame")
        urls_card.grid(row=2, column=0, sticky="nsew", pady=(0, 14))
        urls_card.columnconfigure(0, weight=1)
        urls_card.rowconfigure(1, weight=1)
        ttk.Label(urls_card, text="VIDEO LINKS", style="Section.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 9)
        )
        self.urls = tk.Text(
            urls_card,
            height=5,
            wrap="word",
            font=("Segoe UI", 10),
            background=self.colors["surface"],
            foreground=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="solid",
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["accent"],
            padx=10,
            pady=9,
        )
        self.urls.grid(row=1, column=0, sticky="nsew")
        ttk.Label(
            urls_card,
            text="Paste one or more links. Each URL will be processed in order.",
            style="Hint.TLabel",
        ).grid(row=2, column=0, sticky="w", pady=(7, 0))

        options_card = ttk.Frame(content, padding=16, style="Card.TFrame")
        options_card.grid(row=3, column=0, sticky="nsew", pady=(0, 14))
        options_card.columnconfigure(1, weight=1)
        ttk.Label(options_card, text="DOWNLOAD OPTIONS", style="Section.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 7)
        )

        ttk.Label(options_card, text="Format", style="Field.TLabel").grid(
            row=1, column=0, sticky="w", padx=(0, 20), pady=6
        )
        self.mode = ttk.Combobox(
            options_card,
            state="readonly",
            values=("MP3 audio", "Video", "Both"),
        )
        self.mode.current(0)
        self.mode.grid(row=1, column=1, sticky="ew", pady=6)

        ttk.Label(options_card, text="Video format", style="Field.TLabel").grid(
            row=2, column=0, sticky="w", padx=(0, 20), pady=6
        )
        self.video_format = ttk.Combobox(
            options_card,
            state="readonly",
            values=("AVI", "MP4"),
        )
        self.video_format.current(0)
        self.video_format.grid(row=2, column=1, sticky="ew", pady=6)

        ttk.Label(options_card, text="Video quality", style="Field.TLabel").grid(
            row=3, column=0, sticky="w", padx=(0, 20), pady=6
        )
        self.quality = ttk.Combobox(
            options_card,
            state="readonly",
            values=("360", "480", "720", "1080", "best"),
        )
        self.quality.set("480")
        self.quality.grid(row=3, column=1, sticky="ew", pady=6)

        ttk.Label(options_card, text="Save to", style="Field.TLabel").grid(
            row=4, column=0, sticky="w", padx=(0, 20), pady=6
        )
        folder_row = ttk.Frame(options_card, style="Card.TFrame")
        folder_row.grid(row=4, column=1, sticky="ew", pady=6)
        folder_row.columnconfigure(0, weight=1)
        self.output_dir = tk.StringVar(value=str(DEFAULT_OUTPUT_DIR))
        ttk.Entry(folder_row, textvariable=self.output_dir).grid(row=0, column=0, sticky="ew")
        ttk.Button(folder_row, text="Browse", command=self._browse).grid(
            row=0, column=1, padx=(8, 0)
        )

        self.overwrite = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_card,
            text="Replace files that already exist",
            variable=self.overwrite,
            style="TCheckbutton",
        ).grid(row=5, column=0, columnspan=2, sticky="w", pady=(8, 0))

        progress_card = ttk.Frame(content, padding=16, style="Card.TFrame")
        progress_card.grid(row=4, column=0, sticky="ew", pady=(0, 14))
        progress_card.columnconfigure(0, weight=1)
        self.status = tk.StringVar(value="Ready")
        ttk.Label(progress_card, text="PROGRESS", style="Section.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )
        self.progress = ttk.Progressbar(
            progress_card, maximum=100, mode="determinate", style="Accent.Horizontal.TProgressbar"
        )
        self.progress.grid(row=1, column=0, sticky="ew")
        ttk.Label(progress_card, textvariable=self.status, style="Status.TLabel").grid(
            row=2, column=0, sticky="w", pady=(8, 0)
        )

        activity_card = ttk.Frame(content, padding=16, style="Card.TFrame")
        activity_card.grid(row=5, column=0, sticky="nsew", pady=(0, 14))
        activity_card.columnconfigure(0, weight=1)
        activity_card.rowconfigure(1, weight=1)
        ttk.Label(activity_card, text="ACTIVITY", style="Section.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 9)
        )
        self.activity = tk.Text(
            activity_card,
            height=6,
            state="disabled",
            wrap="word",
            font=("Segoe UI", 9),
            background="#f8f9fa",
            foreground=self.colors["text"],
            relief="flat",
            padx=10,
            pady=8,
        )
        self.activity.grid(row=1, column=0, sticky="nsew")

        footer = ttk.Frame(content, style="App.TFrame")
        footer.grid(row=6, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        ttk.Label(
            footer,
            text="Requires ffmpeg for MP3 conversion and video output",
            style="FooterHint.TLabel",
        ).grid(row=0, column=0, sticky="w")
        self.start_button = ttk.Button(
            footer, text="Start download", command=self._start, style="Accent.TButton"
        )
        self.start_button.grid(row=0, column=1, sticky="e")

        self.root.after(100, self._process_events)

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure("App.TFrame", background=self.colors["background"])
        style.configure("Card.TFrame", background=self.colors["surface"])
        style.configure(
            "Title.TLabel",
            background=self.colors["background"],
            foreground=self.colors["text"],
            font=("Segoe UI", 22, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=self.colors["background"],
            foreground=self.colors["muted"],
            font=("Segoe UI", 10),
        )
        style.configure(
            "Section.TLabel",
            background=self.colors["surface"],
            foreground=self.colors["muted"],
            font=("Segoe UI", 9, "bold"),
        )
        style.configure(
            "Field.TLabel",
            background=self.colors["surface"],
            foreground=self.colors["text"],
            font=("Segoe UI", 10),
        )
        style.configure(
            "Hint.TLabel",
            background=self.colors["surface"],
            foreground=self.colors["muted"],
            font=("Segoe UI", 9),
        )
        style.configure(
            "FooterHint.TLabel",
            background=self.colors["background"],
            foreground=self.colors["muted"],
            font=("Segoe UI", 9),
        )
        style.configure(
            "Status.TLabel",
            background=self.colors["surface"],
            foreground=self.colors["text"],
            font=("Segoe UI", 9),
        )
        style.configure("TCombobox", padding=(8, 6), font=("Segoe UI", 10))
        style.configure("TEntry", padding=(8, 6), font=("Segoe UI", 10))
        style.configure("TCheckbutton", background=self.colors["surface"], font=("Segoe UI", 9))
        style.configure("TButton", padding=(10, 7), font=("Segoe UI", 9))
        style.configure(
            "Accent.TButton",
            background=self.colors["accent"],
            foreground="#ffffff",
            padding=(16, 9),
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
        )
        style.map(
            "Accent.TButton",
            background=[
                ("disabled", "#d8a09c"),
                ("active", self.colors["accent_active"]),
                ("!disabled", self.colors["accent"]),
            ],
            foreground=[("disabled", "#ffffff"), ("!disabled", "#ffffff")],
        )
        style.configure(
            "Accent.Horizontal.TProgressbar",
            background=self.colors["accent"],
            troughcolor="#e9ecef",
            bordercolor="#e9ecef",
            lightcolor=self.colors["accent"],
            darkcolor=self.colors["accent"],
            thickness=8,
        )

    def _browse(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.output_dir.get() or None)
        if selected:
            self.output_dir.set(selected)

    def _append_activity(self, message: str) -> None:
        self.activity.configure(state="normal")
        self.activity.insert("end", message + "\n")
        self.activity.see("end")
        self.activity.configure(state="disabled")

    def _start(self) -> None:
        urls = extract_urls(self.urls.get("1.0", "end"))
        if not urls:
            messagebox.showerror("No URLs", "Paste at least one YouTube URL to download.")
            return

        output_path = self.output_dir.get().strip()
        if not output_path:
            messagebox.showerror("Missing folder", "Choose a folder for downloaded files.")
            return
        output_dir = Path(output_path).expanduser()

        try:
            quality = normalize_quality(self.quality.get())
        except argparse.ArgumentTypeError as exc:
            messagebox.showerror("Invalid quality", str(exc))
            return

        mode_value = {"MP3 audio": "1", "Video": "2", "Both": "3"}[self.mode.get()]
        video_format = self.video_format.get().lower()
        self.start_button.configure(state="disabled")
        self.progress.configure(value=0)
        self.status.set(f"Starting {len(urls)} download(s)...")
        self._append_activity(f"Starting {len(urls)} download(s).")
        threading.Thread(
            target=self._download,
            args=(urls, mode_value, output_dir, quality, video_format, self.overwrite.get()),
            daemon=True,
        ).start()

    def _download(
        self,
        urls: list[str],
        mode: str,
        output_dir: Path,
        quality: str,
        video_format: str,
        overwrite: bool,
    ) -> None:
        failures = 0
        try:
            ensure_output_dir(output_dir)
            setup_logging(output_dir / "downloader.log")
            for index, url in enumerate(urls, start=1):
                self.events.put(("status", f"Processing {index}/{len(urls)}"))
                self.events.put(("activity", f"[{index}/{len(urls)}] {url}"))
                self.events.put(("progress", 0.0))
                try:
                    process_url(
                        url,
                        mode,
                        output_dir,
                        quality,
                        index,
                        overwrite,
                        progress_callback=lambda value: self.events.put(("progress", value)),
                        video_format=video_format,
                    )
                    self.events.put(("activity", f"Finished processing {url}"))
                except Exception as exc:
                    failures += 1
                    LOGGER.exception("Failed to process URL: %s", url)
                    self.events.put(("activity", f"Error processing {url}: {exc}"))

            completed = len(urls) - failures
            self.events.put(
                (
                    "done",
                    f"Processed {completed} URL(s); {failures} request error(s). "
                    f"See log: {output_dir / 'downloader.log'}",
                )
            )
        except Exception as exc:
            LOGGER.exception("Could not start download")
            self.events.put(("error", str(exc)))

    def _process_events(self) -> None:
        while True:
            try:
                event, value = self.events.get_nowait()
            except queue.Empty:
                break

            if event == "progress":
                self.progress.configure(value=max(0, min(100, float(value))))
            elif event == "status":
                self.status.set(str(value))
            elif event == "activity":
                self._append_activity(str(value))
            elif event == "error":
                self.status.set("Could not start downloads")
                self._append_activity(f"Error: {value}")
                messagebox.showerror("Download error", str(value))
                self.start_button.configure(state="normal")
            elif event == "done":
                self.status.set(str(value))
                self._append_activity(str(value))
                self.start_button.configure(state="normal")

        self.root.after(100, self._process_events)


def main() -> None:
    root = tk.Tk()
    DownloaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
