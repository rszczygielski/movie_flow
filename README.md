# MovieFlow 🎬

**MovieFlow** is a powerful, automated media preparation workflow and orchestrator. It acts as a localized "media forge," designed to automatically analyze and transcode video files, download Polish subtitles via NapiProjekt, and push them through a robust processing pipeline (encoding fixes, text sanitization, frame shifting, and MicroDVD to SRT conversion).

## ✨ Features

* **Smart Directory Scanning:** Provide a directory, and the orchestrator automatically detects the main video file (ignoring samples) and the corresponding subtitle file.
* **Video Analysis & Transcoding:** Uses `ffprobe` to analyze codecs and pixel formats. If the video is not optimally formatted (e.g., HEVC/x265 or 10-bit), it automatically transcodes it to highly compatible **H.264 8-bit (yuv420p)** using `ffmpeg`.
* **NapiProjekt Integration:** Automatically downloads the correct Polish subtitles based on the video file hash or a manually provided NapiProjekt hash using the `napi-py` API.
* **Subtitle Processing Pipeline:**
  * **Encoding Fixer:** Repairs broken Polish characters (e.g., CP1250/ISO-8859-2 to UTF-8).
  * **Text Sanitizer:** Removes unwanted metadata, HTML tags, or emojis.
  * **Auto-Shifter:** Shifts subtitle timings backward or forward by a specified millisecond delta.
  * **Format Converter:** Seamlessly converts legacy MicroDVD format (`{start}{end}`) to standard `.srt` using accurate framerate math.

## ⚙️ Prerequisites

Before you begin, ensure you have the following installed on your system:
* **Python 3.10+**
* **FFmpeg & FFprobe:** Required for video analysis and transcoding.
  * *Ubuntu/Debian:* `sudo apt install ffmpeg`
  * *macOS:* `brew install ffmpeg`
  * *Windows:* Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) and add to system PATH.

## 🚀 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/rszczygielski/movie_flow
   cd movie_flow