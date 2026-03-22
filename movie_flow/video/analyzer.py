import subprocess
import json
import logging
from pathlib import Path

class VideoAnalyzer:
    """
    Analyzes video files using ffprobe to extract stream information.
    """

    def get_video_stream_info(self, video_path: str) -> dict:
        """
        Extracts video stream metadata using ffprobe.

        Args:
            video_path (str): Path to the video file.

        Returns:
            dict: Dictionary containing video stream properties (e.g., codec_name, pix_fmt).
                  Returns empty dict if analysis fails.
        """
        if not Path(video_path).exists():
            logging.error(f"Video file does not exist: {video_path}")
            return {}

        command = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_entries", "stream=codec_name,pix_fmt",
            "-select_streams", "v:0", # Select only the first video stream
            video_path
        ]

        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                streams = data.get("streams", [])
                if streams:
                    return streams[0]
            else:
                logging.error(f"ffprobe failed: {result.stderr}")
        except FileNotFoundError:
            logging.error("ffprobe is not installed or not added to system PATH.")
        except json.JSONDecodeError:
            logging.error("Failed to parse ffprobe output.")

        return {}

    def needs_h264_8bit_conversion(self, video_path: str) -> bool:
        """
        Checks if the video requires conversion to H.264 8-bit.

        Args:
            video_path (str): Path to the video file.

        Returns:
            bool: True if conversion is needed, False if it's already H.264 8-bit.
        """
        info = self.get_video_stream_info(video_path)
        if not info:
            logging.warning("Could not analyze video, assuming conversion is NOT needed to be safe.")
            return False

        codec = info.get("codec_name")
        pix_fmt = info.get("pix_fmt")

        logging.debug(f"Analyzed video {video_path} - Codec: {codec}, Pixel Format: {pix_fmt}")

        # H.264 uses codec 'h264', and 8-bit color space usually corresponds to 'yuv420p'
        if codec != "h264" or pix_fmt != "yuv420p":
            return True

        return False