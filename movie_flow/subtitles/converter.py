import re
import logging
from datetime import timedelta
from .base import BaseProcessor

class MicroDvdToSrtConverter(BaseProcessor):
    """
    Converts MicroDVD format ({start}{end}text) to standard SRT format.
    """

    MICRODVD_PATTERN = re.compile(r"^\{(\d+)\}\{(\d+)\}(.*)")

    def __init__(self, fps: float = 23.976):
        """
        Initializes the converter with a specific framerate.

        Args:
            fps (float): Frames per second of the video. Defaults to 23.976.
        """
        self.fps = fps
        logging.debug(f"MicroDvdToSrtConverter initialized with FPS: {self.fps}")

    def _frame_to_timestamp(self, frame: int) -> str:
        """
        Converts a frame number to an SRT timestamp.

        Args:
            frame (int): The frame number.

        Returns:
            str: Timestamp in 'HH:MM:SS,mmm' format.
        """
        total_seconds = frame / self.fps
        td = timedelta(seconds=total_seconds)

        seconds_int = int(td.total_seconds())
        hours, remainder = divmod(seconds_int, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = int(td.microseconds / 1000)

        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

    def process(self, content: str) -> str:
        """
        Converts the entire MicroDVD content to SRT.

        Args:
            content (str): MicroDVD formatted subtitle content.

        Returns:
            str: SRT formatted subtitle content.
        """
        logging.info("Starting MicroDVD to SRT conversion...")

        lines = content.splitlines()
        output = []
        subtitle_index = 1
        unmatched_lines = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            match = self.MICRODVD_PATTERN.match(line)
            if match:
                start_frame = int(match.group(1))
                end_frame = int(match.group(2))
                text = match.group(3)

                start_time = self._frame_to_timestamp(start_frame)
                end_time = self._frame_to_timestamp(end_frame)

                # Replace MicroDVD line breaks with actual newlines
                text_formatted = text.replace('|', '\n')

                output.append(f"{subtitle_index}")
                output.append(f"{start_time} --> {end_time}")
                output.append(text_formatted)
                output.append("") # Empty line after each block

                subtitle_index += 1
            else:
                # If a line doesn't match MicroDVD, we append it as-is
                # (helps with broken lines or metadata)
                unmatched_lines += 1
                logging.debug(f"Line did not match MicroDVD pattern, appending as-is: '{line}'")
                output.append(line)

        total_lines = len(lines)
        converted_blocks = subtitle_index - 1

        # A single, consistent summary always logged at the INFO level
        logging.info(
            f"Conversion summary -> "
            f"Total lines: {total_lines} | "
            f"Converted blocks: {converted_blocks} | "
            f"Unmatched lines: {unmatched_lines}"
        )

        # If there are any unmatched lines, we can leave an additional trace,
        # but only at the DEBUG level (so it doesn't clutter the standard logs).
        if unmatched_lines > 0:
            logging.debug("Some lines did not match the MicroDVD format. They were appended as-is.")

        return "\n".join(output)