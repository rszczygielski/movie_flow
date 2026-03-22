import sys
import logging
import configparser
from pathlib import Path

# --- Video Imports ---
from video.analyzer import VideoAnalyzer
from video.transcoder import VideoTranscoder

# --- Subtitle Imports ---
from subtitles.downloader import NapiDownloader
from core.pipeline import SubtitlePipeline
from subtitles.cleaners import PolishEncodingFixer, TextSanitizer
from subtitles.shifter import AutoSubtitleShifter
from subtitles.converter import MicroDvdToSrtConverter

class MediaOrchestrator:
    """
    Orchestrates media tasks based on configuration settings.
    Manages the workflow between video analysis, transcoding, and subtitle processing.
    """

    def __init__(self, config: configparser.ConfigParser):
        """
        Initializes the orchestrator with the provided configuration.
        """
        logging.debug("Initializing MediaOrchestrator...")
        self.config = config

        # Extract main paths from the configuration
        self.media_folder = config.get("Paths", "media_folder", fallback="").strip()
        self.video_file = config.get("Paths", "video_file").strip()
        self.subtitle_file_override = config.get("Paths", "subtitle_file", fallback="").strip()

        # State variable to share data between tasks (e.g., passing the downloaded subtitle path to the processor)
        self.active_subtitle_path = None

        logging.debug(f"Target video file set to: {self.video_file}")
        logging.debug(f"Subtitle override path provided: {self.subtitle_file_override}")

    def execute(self):
        """
        Evaluates the configuration and runs the enabled tasks in the correct logical order.
        """
        logging.info("Starting Orchestrator execution sequence.")

        # 1. Resolve paths (Auto-detect from folder if provided)
        self._scan_media_folder()

        # Ensure the main video file actually exists before doing anything
        if not Path(self.video_file).exists():
            logging.error(f"Execution aborted: Main video file not found at '{self.video_file}'")
            return

        # Check configuration flags for each task
        run_analyze = self.config.getboolean("Tasks", "analyze_video")
        run_transcode = self.config.getboolean("Tasks", "transcode_video")
        run_download = self.config.getboolean("Tasks", "download_subtitles")
        run_process = self.config.getboolean("Tasks", "process_subtitles")

        logging.debug(f"Task status - Analyze: {run_analyze}, Transcode: {run_transcode}, Download: {run_download}, Process Subs: {run_process}")

        # 1. Analyze video properties
        if run_analyze:
            self._analyze_video()

        # 2. Transcode video if requested
        if run_transcode:
            self._transcode_video()

        # 3. Download subtitles
        if run_download:
            self._download_subtitles()

        # 4. Process subtitles (fix encoding, shift, convert)
        if run_process:
            self._process_subtitles()

        logging.info("All selected orchestration tasks have been executed successfully.")

    def _scan_media_folder(self):
            """
            Scans the provided media directory to auto-detect the main video file
            and subtitle file. Strictly enforces a maximum of ONE video file and ONE
            subtitle file. Exits the program immediately if multiples are found.
            """
            if not getattr(self, 'media_folder', None) or not Path(self.media_folder).is_dir():
                logging.debug("No valid media_folder provided. Falling back to explicit file paths.")
                return

            logging.info(f"Scanning media folder: {self.media_folder}")
            folder_path = Path(self.media_folder)

            # Delegate tasks to helper methods
            self._detect_video_file(folder_path)
            self._detect_subtitle_file(folder_path)

    def _detect_video_file(self, folder_path: Path):
        """
        Helper method to detect a single video file in the given folder.
        """
        video_exts = {'.mkv', '.mp4', '.avi'}
        video_files = [
            f for f in folder_path.iterdir()
            if f.is_file() and f.suffix.lower() in video_exts
        ]

        if len(video_files) > 1:
            logging.error(f"FATAL ERROR: Found {len(video_files)} video files in the folder. Strictly ONE is allowed. Exiting.")
            sys.exit(1)

        elif len(video_files) == 1:
            self.video_file = str(video_files[0])
            logging.info(f"Auto-detected main video file: {video_files[0].name}")
        else:
            logging.warning("No video files found in the specified media_folder.")

    def _detect_subtitle_file(self, folder_path: Path):
        """
        Helper method to detect a single subtitle file in the given folder.
        """
        subtitle_exts = {'.txt', '.srt'}
        subtitle_files = [
            f for f in folder_path.iterdir()
            if f.is_file() and f.suffix.lower() in subtitle_exts
        ]

        if len(subtitle_files) > 1:
            logging.error(f"FATAL ERROR: Found {len(subtitle_files)} subtitle files in the folder. Strictly ONE is allowed. Exiting.")
            sys.exit(1)

        elif len(subtitle_files) == 1:
            self.active_subtitle_path = str(subtitle_files[0])
            logging.info(f"Auto-detected subtitle file: {subtitle_files[0].name}")
        else:
            logging.info("No unprocessed subtitle files found in the media_folder.")

    def _analyze_video(self):
        """Handles video metadata extraction and analysis."""
        logging.info("--- TASK: ANALYZE VIDEO ---")
        analyzer = VideoAnalyzer()

        logging.debug(f"Requesting stream info for: {self.video_file}")
        info = analyzer.get_video_stream_info(self.video_file)

        if not info:
            logging.warning("Could not extract video information. Check if the file is a valid video format.")
            logging.info("-" * 30)
            return
        codec = info.get("codec_name", "unknown")
        pix_fmt = info.get("pix_fmt", "unknown")
        logging.info(f"Video Info -> Codec: {codec}, Pixel Format: {pix_fmt}")

        # Check if the video meets our target optimal format (H.264 8-bit)
        if analyzer.needs_h264_8bit_conversion(self.video_file):
            logging.info("Conclusion: Video requires conversion to H.264 8-bit (yuv420p).")
        else:
            logging.info("Conclusion: Video is already in optimal format.")
        logging.info("-" * 30)

    def _transcode_video(self):
        """Handles video transcoding to the target format."""
        logging.info("--- TASK: TRANSCODE VIDEO ---")
        transcoder = VideoTranscoder()

        video_path_obj = Path(self.video_file)

        # Generate the output filename by appending ' H264' to the original stem
        # e.g., 'Movie.mkv' -> 'Movie H264.mkv'
        output_video_path = video_path_obj.with_name(f"{video_path_obj.stem} H264{video_path_obj.suffix}")

        logging.debug(f"Target transcode output path: {output_video_path}")

        success = transcoder.convert_to_h264_8bit(self.video_file, str(output_video_path))
        if success:
            logging.info(f"Transcoding finished successfully. Saved as: {output_video_path}")
        else:
            logging.error("Transcoding failed. Check previous FFmpeg logs for details.")

        logging.info("-" * 30)

    def _download_subtitles(self):
        """Handles downloading subtitles via the NapiProjekt database."""
        logging.info("--- TASK: DOWNLOAD SUBTITLES ---")
        downloader = NapiDownloader()

        logging.debug("Initiating subtitle download sequence...")
        self.napi_hash = self.config.get("Paths", "napi_hash").strip()

        if self.napi_hash:
            downloaded_path = downloader.download_by_hash(self.napi_hash, self.media_folder)
        else:
            downloaded_path = downloader.download_by_video_path(self.video_file)

        if downloaded_path:
            # Store the downloaded path in the state variable so the processing task can use it
            self.active_subtitle_path = downloaded_path
            logging.info(f"Subtitles downloaded and registered in orchestrator state: {self.active_subtitle_path}")
        else:
            logging.warning("Subtitle download failed or no subtitles were found for this video.")

        logging.info("-" * 30)

    def _process_subtitles(self):
        """Handles the text processing pipeline for subtitles."""
        logging.info("--- TASK: PROCESS SUBTITLES ---")

        if not self.active_subtitle_path:
            if self.subtitle_file_override and Path(self.subtitle_file_override).exists():
                self.active_subtitle_path = self.subtitle_file_override
                logging.info(f"Using subtitle file from config override: {self.active_subtitle_path}")

        if not self.active_subtitle_path:
            logging.error("No subtitle file found to process. Did you forget to download or set the path in config?")
            return

        logging.debug(f"Proceeding to process subtitle file: {self.active_subtitle_path}")

        # Assemble the pipeline based on configuration toggles
        processors_list = self._build_processor_list()

        if not processors_list:
            logging.warning("No subtitle processors enabled in config. Skipping processing task.")
            return

        logging.debug(f"Initializing SubtitlePipeline with {len(processors_list)} processors.")
        pipeline = SubtitlePipeline(processors=processors_list)

        # Determine the correct file extension for the output
        # If we are converting MicroDVD to SRT, we MUST save it as .srt
        convert_to_srt = self.config.getboolean("SubtitleProcessing", "convert_to_srt")
        out_ext = ".srt" if convert_to_srt else Path(self.active_subtitle_path).suffix

        # # Append '_PL' to the original filename to avoid overwriting the source subtitle file
        # output_sub_path = Path(self.active_subtitle_path).with_name(f"{Path(self.active_subtitle_path).stem}_PL{out_ext}")

        # logging.debug(f"Output subtitle will be saved to: {output_sub_path}")

        try:
            pipeline.execute(self.active_subtitle_path, self.active_subtitle_path)
            logging.info("Subtitle processing pipeline finished successfully.")
        except Exception as e:
            logging.error(f"Subtitle processing pipeline failed: {e}")

        logging.info("-" * 30)


    def _build_processor_list(self):
        """
        Helper method to read the configuration and build a list of processor objects.
        Returns:
            list: A list of instantiated BaseProcessor objects.
        """
        processors = []
        fps = self.config.getfloat("VideoSettings", "fps")
        shift_ms = self.config.getint("SubtitleProcessing", "shift_ms")

        logging.debug("Building subtitle processor list based on configuration...")

        if self.config.getboolean("SubtitleProcessing", "fix_encoding"):
            logging.debug("Adding PolishEncodingFixer to pipeline.")
            processors.append(PolishEncodingFixer())

        if self.config.getboolean("SubtitleProcessing", "sanitize_text"):
            logging.debug("Adding TextSanitizer to pipeline.")
            processors.append(TextSanitizer())

        if shift_ms != 0:
            logging.debug(f"Adding AutoSubtitleShifter to pipeline (Shift: {shift_ms}ms, FPS: {fps}).")
            processors.append(AutoSubtitleShifter(delta_ms=shift_ms, fps=fps))

        if self.config.getboolean("SubtitleProcessing", "convert_to_srt"):
            logging.debug(f"Adding MicroDvdToSrtConverter to pipeline (FPS: {fps}).")
            processors.append(MicroDvdToSrtConverter(fps=fps))

        logging.debug(f"Successfully built pipeline with {len(processors)} processors.")
        return processors