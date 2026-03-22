import os
import logging
from pathlib import Path
from napi import NapiPy

class NapiDownloader:
    """
    Handles downloading subtitles using the native napi-py Python API.
    """

    def download_by_video_path(self, video_path: str) -> str | None:
        """
        Downloads subtitles based on the video file's hash and saves them next to the video.

        Args:
            video_path (str): Path to the video file.

        Returns:
            str | None: The path to the downloaded subtitles file, or None if the download failed.
        """
        full_video_path = Path(video_path).expanduser().resolve()

        if not full_video_path.exists():
            logging.error(f"Video file does not exist: {full_video_path}")
            return None

        logging.info(f"Attempting to download subtitles for video: {full_video_path}")

        try:
            napi = NapiPy()

            # 1. Calculate the video file hash
            logging.debug("Calculating file hash...")
            movie_hash = napi.calc_hash(str(full_video_path))
            logging.debug(f"Hash calculated: {movie_hash}")

            # 2. Fetch the temporary subtitle file
            tmp_file = self._fetch_tmp_subs(movie_hash, napi)
            if not tmp_file:
                logging.warning(f"No subtitles found in NapiProjekt database for {full_video_path.name}")
                return None

            # 3. Move subtitles from the temporary directory to the movie directory
            logging.debug("Moving downloaded subtitles to the movie directory...")
            subs_path = napi.move_subs_to_movie(tmp_file, str(full_video_path))

            logging.info(f"Subtitles successfully downloaded and saved to: {subs_path}")
            return subs_path

        except ImportError:
            self._log_import_error()
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred while downloading subtitles by path: {e}")
            return None

    def download_by_hash(self, movie_hash: str, output_path: str) -> str | None:
        """
        Downloads subtitles using an explicitly provided NapiProjekt hash.

        Args:
            movie_hash (str): The exact NapiProjekt hash of the video.
            output_path (str): The exact file path where the subtitles should be saved (e.g., '/path/subs.txt').

        Returns:
            str | None: The path to the downloaded subtitles file, or None if the download failed.
        """
        logging.info(f"Attempting to download subtitles for explicit hash: {movie_hash}")

        try:
            napi = NapiPy()

            # 1. Fetch the temporary subtitle file
            tmp_file = self._fetch_tmp_subs(movie_hash, napi)
            if not tmp_file:
                logging.warning(f"No subtitles found in NapiProjekt database for hash {movie_hash}")
                return None

            # 2. Move and rename the temporary file to the requested output path
            output_file = Path(output_path).expanduser().resolve()
            output_file.parent.mkdir(parents=True, exist_ok=True)

            logging.debug(f"Moving downloaded subtitles to specific path: {output_file}")
            subs_path = napi.move_subs_to_movie(tmp_file, str(output_file))

            logging.info(f"Subtitles successfully downloaded and saved to: {subs_path}")
            return subs_path

        except ImportError:
            self._log_import_error()
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred while downloading subtitles by hash: {e}")
            return None

    def _fetch_tmp_subs(self, movie_hash: str, napi_instance: NapiPy) -> str | None:
        """
        Helper method to communicate with the NapiPy API and fetch the temp file.

        Args:
            movie_hash (str): The hash of the movie.
            napi_instance (NapiPy): An active instance of the NapiPy client.

        Returns:
            str | None: Path to the temporary subtitle file, or None if not found.
        """
        logging.debug("Fetching subtitles from NapiProjekt API...")
        source_encoding, target_encoding, tmp_file = napi_instance.download_subs(movie_hash)
        logging.debug(f"API response - Source Encoding: {source_encoding}, Target Encoding: {target_encoding}, Temp File: {tmp_file}")

        if not tmp_file or not os.path.exists(tmp_file):
            return None

        return tmp_file

    def _log_import_error(self):
        """Helper to log missing dependency error."""
        logging.error("The 'napi-py' library is not installed. Please run 'pip install napi-py'.")