import subprocess
import logging
from pathlib import Path

class VideoTranscoder:
    """
    Handles video transcoding operations using FFmpeg.
    """

    def convert_to_h264_8bit(self, input_path: str, output_path: str) -> bool:
        """
        Converts video to H.264 8-bit using specific FFmpeg parameters.
        Copies audio and subtitle streams as-is.

        Args:
            input_path (str): Path to the source video.
            output_path (str): Path for the output converted video.

        Returns:
            bool: True if conversion was successful, False otherwise.
        """
        if not Path(input_path).exists():
            logging.error(f"Source video does not exist: {input_path}")
            return False

        logging.info(f"Starting H.264 8-bit conversion for: {input_path}")
        logging.info(f"Output will be saved to: {output_path}")

        command = [
            "ffmpeg",
            "-y",                   # Overwrite output files without asking
            "-i", input_path,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",  # Enforce 8-bit
            "-c:a", "copy",         # Copy audio
            "-c:s", "copy",         # Copy embedded subtitles
            output_path
        ]

        try:
            # We don't capture stdout/stderr here so the user can see FFmpeg's progress bar in the terminal
            result = subprocess.run(command)

            if result.returncode == 0:
                logging.info("Video conversion completed successfully.")
                return True
            else:
                logging.error(f"FFmpeg exited with error code {result.returncode}")
                return False

        except FileNotFoundError:
            logging.error("ffmpeg is not installed or not added to system PATH.")
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred during transcoding: {e}")
            return False