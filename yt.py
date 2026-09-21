import sys
try:
    import audioop
except ImportError:
    try:
        import audioop_lts
        sys.modules['audioop'] = audioop_lts
        sys.modules['pyaudioop'] = audioop_lts
    except ImportError:
        pass

from pytubefix import YouTube
import subprocess
import os
import re

directory = "D:/Lagu"

if not os.path.exists(directory):
    os.makedirs(directory)
    print(f"Created directory: {directory}")

def show_menu():
    print("\n" + "=" * 35)
    print("      YouTube Downloader")
    print("=" * 35)
    print("  [1] Download MP3 (Audio only)")
    print("  [2] Download AVI (Video - Xvid / MP3 - 480p)")
    print("  [3] Download Both")
    print("=" * 35)
    while True:
        choice = input("Select an option: ").strip()
        if choice in ("1", "2", "3"):
            return choice
        print("Invalid choice. Please enter 1, 2, or 3.")

def get_urls():
    print("\nEnter YouTube URLs (you can paste them concatenated together).\n")
    urls = []
    raw_input = input("  URLs: ").strip()
    spaced_input = raw_input.replace('https', ' https')
    found_links = re.findall(r'(https?://[^\s]+)', spaced_input)
    
    for link in found_links:
        clean_link = link.strip()
        if clean_link.endswith('http'):
            clean_link = clean_link[:-4]
        if clean_link.endswith('https'):
            clean_link = clean_link[:-5]
        if clean_link and clean_link not in urls:
            urls.append(clean_link)
            
    print(f"  Detected {len(urls)} URL(s)")
    return urls

def on_progress(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage = (bytes_downloaded / total_size) * 100
    print(f"\r  -> Progress: {percentage:.1f}%", end="", flush=True)

def clean_filename(title, index):
    ascii_name = title.encode('ascii', 'ignore').decode('ascii')
    safe_name = "".join(c for c in ascii_name if c.isalnum() or c in (' ', '-', '_')).strip()
    if not safe_name:
        safe_name = f"Video_{index}"
    return safe_name[:40]

def convert_to_mp3(input_file, output_dir, safe_name):
    try:
        output_file = os.path.join(output_dir, safe_name + ".mp3")
        command = [
            "ffmpeg", "-y", "-i", input_file, 
            "-q:a", "0", "-map", "a", output_file
        ]
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"\n  -> Converted to: '{output_file}'")
        os.remove(input_file)
    except Exception as e:
        print(f"\n  Error converting to MP3: {e}")

def download_mp3(yt, output_dir, safe_name):
    ys = yt.streams.get_audio_only()
    if not ys:
        print("  -> Error: No audio stream available.")
        return
    expected_filename = safe_name + ".mp3"
    if os.path.exists(os.path.join(output_dir, expected_filename)):
        print(f"  -> Skipped: '{expected_filename}' already exists.")
        return

    print("  -> Downloading audio...")
    file_path = ys.download(output_path=output_dir)
    convert_to_mp3(file_path, output_dir, safe_name)

def download_avi(yt, output_dir, safe_name):
    video_stream = yt.streams.filter(res="480p", only_video=True).first()
    if not video_stream:
        video_stream = yt.streams.filter(only_video=True).order_by('resolution').desc().first()
    audio_stream = yt.streams.get_audio_only()
    
    if not video_stream or not audio_stream:
        print("  -> Error: Could not find valid streams.")
        return
        
    expected_filename = safe_name + ".avi"
    final_path = os.path.join(output_dir, expected_filename)
    if os.path.exists(final_path):
        print(f"  -> Skipped: '{expected_filename}' already exists.")
        return

    print("  -> Downloading video stream...")
    video_path = video_stream.download(output_path=output_dir, filename="temp_vid.mp4")
    print("\n  -> Downloading audio stream...")
    audio_path = audio_stream.download(output_path=output_dir, filename="temp_aud.m4a")
    print("\n  -> Merging and converting to AVI...")
    
    command = [
        "ffmpeg", "-y", 
        "-i", video_path, 
        "-i", audio_path, 
        "-c:v", "mpeg4", 
        "-vtag", "xvid",
        "-q:v", "3", 
        "-vf", "scale=854:480:force_original_aspect_ratio=decrease,pad=854:480:(ow-iw)/2:(oh-ih)/2,fps=30",
        "-c:a", "libmp3lame", 
        "-ar", "44100", 
        "-ac", "2",
        "-b:a", "128k", 
        final_path
    ]
    
    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"  -> Saved to: '{final_path}'")
        os.remove(video_path)
        os.remove(audio_path)
    except Exception as e:
        print(f"  -> Error merging: {e}")
        if os.path.exists(video_path): os.remove(video_path)
        if os.path.exists(audio_path): os.remove(audio_path)

print("\n" + "=" * 35)
print("      YouTube Downloader")
print("=" * 35)

while True:
    urls = get_urls()
    if not urls:
        print("No URLs detected. Try again.")
        continue
        
    choice = show_menu()
    print(f"\nStarting download for {len(urls)} video(s)...\n")
    
    for i, url in enumerate(urls, 1):
        try:
            print(f"[{i}/{len(urls)}] Processing: {url}")
            yt = YouTube(url, on_progress_callback=on_progress)
            print(f"  Title: {yt.title}")
            
            safe_name = clean_filename(yt.title, i)
            
            if choice == "1":
                download_mp3(yt, directory, safe_name)
            elif choice == "2":
                download_avi(yt, directory, safe_name)
            elif choice == "3":
                download_mp3(yt, directory, safe_name)
                download_avi(yt, directory, safe_name)
        except Exception as e:
            print(f"  Error processing {url}: {e}")
            
    print("\nAll downloads complete!")
    again = input("\nDownload more videos? (y/n): ").strip().lower()
    if again != "y":
        print("Goodbye!")
        break