import re
import logging
from datetime import timedelta
from .base import BaseProcessor

class SrtShifter(BaseProcessor):
    """
    Shifts timestamps specifically for SRT formatted subtitles.
    """

    SRT_PATTERN = re.compile(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})")

    def __init__(self, delta_ms: int):
        """
        Initializes the SRT shifter.

        Args:
            delta_ms (int): Shift amount in milliseconds (positive or negative).
        """
        self.delta = timedelta(milliseconds=delta_ms)
        logging.debug(f"SrtShifter initialized with delta: {self.delta}")

    @staticmethod
    def _parse_timestamp(timestamp: str) -> timedelta:
        h, m, s_ms = timestamp.split(":")
        s, ms = s_ms.split(",")
        return timedelta(hours=int(h), minutes=int(m), seconds=int(s), milliseconds=int(ms))

    @staticmethod
    def _format_timestamp(td: timedelta) -> str:
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = int(td.microseconds / 1000)
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

    def _adjust_timestamp(self, timestamp: str) -> str:
        new_time = self._parse_timestamp(timestamp) + self.delta
        new_time = max(new_time, timedelta())
        return self._format_timestamp(new_time)

    def process(self, content: str) -> str:
        if self.delta.total_seconds() == 0:
            logging.info("SRT Shift delta is 0. Skipping shifting process.")
            return content

        logging.info(f"Applying SRT timestamp shift: {self.delta.total_seconds()} seconds.")

        lines = content.splitlines()
        output = []

        for line in lines:
            match = self.SRT_PATTERN.search(line)
            if match:
                new_start = self._adjust_timestamp(match.group(1))
                new_end = self._adjust_timestamp(match.group(2))
                output.append(f"{new_start} --> {new_end}")
            else:
                output.append(line)

        return "\n".join(output)


class MicroDvdShifter(BaseProcessor):
    """
    Shifts timestamps specifically for MicroDVD formatted subtitles.
    """

    MICRODVD_PATTERN = re.compile(r"^\{(\d+)\}\{(\d+)\}(.*)")

    def __init__(self, delta_ms: int, fps: float = 23.976):
        """
        Initializes the MicroDVD shifter.

        Args:
            delta_ms (int): Shift amount in milliseconds (positive or negative).
            fps (float): Frames per second to calculate frame shift.
        """
        self.frame_shift = int((delta_ms / 1000.0) * fps)
        logging.debug(f"MicroDvdShifter initialized. Delta: {delta_ms}ms, FPS: {fps}, Calculated frame shift: {self.frame_shift}")

    def process(self, content: str) -> str:
        if self.frame_shift == 0:
            logging.info("MicroDVD frame shift is 0. Skipping shifting process.")
            return content

        logging.info(f"Applying MicroDVD frame shift: {self.frame_shift} frames.")

        lines = content.splitlines()
        output = []

        for line in lines:
            match = self.MICRODVD_PATTERN.match(line)
            if match:
                start_frame = max(0, int(match.group(1)) + self.frame_shift)
                end_frame = max(0, int(match.group(2)) + self.frame_shift)
                text = match.group(3)
                output.append(f"{{{start_frame}}}{{{end_frame}}}{text}")
            else:
                output.append(line)

        return "\n".join(output)


class AutoSubtitleShifter(BaseProcessor):
    """
    Auto-detects the subtitle format and delegates shifting to the correct class.
    """

    def __init__(self, delta_ms: int, fps: float = 23.976):
        """
        Initializes the auto-shifter.

        Args:
            delta_ms (int): Shift amount in milliseconds.
            fps (float): Frames per second (used if format is MicroDVD).
        """
        self.delta_ms = delta_ms
        self.fps = fps

    def process(self, content: str) -> str:
        """
        Detects format by analyzing the content and processes it.
        """
        logging.info("AutoSubtitleShifter: Analyzing subtitle format...")

        # Quick check if there are any MicroDVD formatted brackets at the start of a line
        is_microdvd = bool(re.search(r"^\{\d+\}\{\d+\}", content, re.MULTILINE))

        if is_microdvd:
            logging.info("Detected format: MicroDVD. Delegating to MicroDvdShifter.")
            shifter = MicroDvdShifter(delta_ms=self.delta_ms, fps=self.fps)
        else:
            logging.info("Detected format: SRT (or unknown). Delegating to SrtShifter.")
            shifter = SrtShifter(delta_ms=self.delta_ms)

        return shifter.process(content)