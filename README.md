# YouTube Downloader

Script Python sederhana untuk mengunduh video/audio dari YouTube dan menyimpannya ke folder lokal.

## Fitur

- Download audio hanya dalam format MP3
- Download video dalam format AVI dengan kualitas 480p (jika stream tersedia)
- Download sekaligus audio dan video
- Mendukung banyak URL sekaligus dalam satu input
- Secara otomatis mendeteksi link YouTube dari teks yang Anda tempel
- Menghindari duplikasi file jika file dengan nama yang sama sudah ada
- Menggunakan ffmpeg untuk konversi dan merge audio/video

## Persyaratan

Pastikan perangkat Anda sudah memiliki:

- Python 3.x
- ffmpeg terinstal dan tersedia di PATH
- paket `pytubefix`

Install paket yang dibutuhkan:

```bash
pip install pytubefix
```

Jika ffmpeg belum terinstal, instal terlebih dahulu dan pastikan perintah `ffmpeg` bisa dijalankan dari terminal/command prompt.

## Cara Menjalankan

1. Buka file `yt.py`
2. Sesuaikan folder tujuan jika diperlukan:

```python
DEFAULT_OUTPUT_DIR = Path("D:/Lagu")
```

3. Jalankan program dalam mode interaktif:

```bash
python yt.py
```

### Mode CLI (lebih profesional untuk penggunaan otomatis)

```bash
python yt.py --mode mp3 --quality 480 --urls "https://youtu.be/abc123" "https://www.youtube.com/watch?v=xyz456"
python yt.py --mode avi --quality 720 --output-dir "D:/Lagu"
python yt.py --mode both --quality 1080 --urls "https://youtu.be/abc123" --overwrite
```

#### Opsi CLI yang tersedia

- `--mode`: `mp3`, `avi`, atau `both`
- `--quality`: `360`, `480`, `720`, `1080`, atau `best`
- `--output-dir`: folder tujuan download
- `--overwrite`: menimpa file yang sudah ada
- `--urls`: daftar URL YouTube
- `--log-file`: lokasi file log (default: `<output-dir>/downloader.log`)

## Log

Aktivitas download disimpan ke `downloader.log` di folder output. Log mencatat waktu,
URL dan judul video, progres per 10%, file yang dilewati, serta hasil atau error konversi.
Lokasi log bisa diubah dengan opsi `--log-file`:

```bash
python yt.py --mode avi --quality 720 --urls "https://youtu.be/abc123" --log-file "D:/Logs/youtube.log"
```

## Mengatasi pesan "request was detected as a bot"

Script memakai client `WEB` pytubefix untuk mendukung pembuatan PO token otomatis.
Pastikan pytubefix versi terbaru:

```bash
python -m pip install --upgrade pytubefix
```

YouTube masih dapat menolak permintaan berdasarkan IP atau keadaan sesi, jadi client ini
tidak menjamin semua permintaan akan berhasil. Baca [panduan PO token pytubefix](https://pytubefix.readthedocs.io/en/latest/user/po_token.html)
untuk penjelasan dan opsi resmi lainnya.

## Cara Pakai

Saat program berjalan:

- Masukkan satu atau lebih URL YouTube
- Bisa paste beberapa link sekaligus dalam satu baris, satu per spasi/line break
- Pilih menu:
  - `1` = Download MP3
  - `2` = Download AVI (480p)
  - `3` = Download Both (MP3 + AVI)

Contoh input:

```text
https://www.youtube.com/watch?v=abc123
https://youtu.be/xyz456
```

## Output

File akan disimpan ke folder yang diatur di variabel `directory`.

Secara default, folder yang digunakan adalah:

```text
D:/Lagu
```

Jika folder belum ada, program akan membuatnya otomatis.

## Catatan

- Nama file akan dibersihkan agar aman untuk sistem file
- Saat memilih opsi `2` atau `3`, script akan mencoba mengambil stream video 480p dan menggabungkan dengan audio ke format AVI
- Jika stream yang dibutuhkan tidak tersedia, program akan menampilkan pesan error yang sesuai

## Penyesuaian Opsional

Anda bisa mengubah pengaturan di dalam script, misalnya:

- folder keluaran (`directory`)
- kualitas video (misalnya dari 480p ke resolusi lain jika diperlukan)
- parameter ffmpeg sesuai kebutuhan Anda

## Lisensi

Proyek ini bersifat open source dan dapat Anda modifikasi sesuai kebutuhan.
