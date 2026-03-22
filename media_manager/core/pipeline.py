import logging
from pathlib import Path
from typing import List
from subtitles.base import BaseProcessor

class SubtitlePipeline:
    """
    Manages the reading, processing, and writing of subtitle files.
    Applies a sequence of processors to the file content.
    """

    def __init__(self, processors: List[BaseProcessor]):
        """
        Initializes the pipeline with a list of processors.

        Args:
            processors (List[BaseProcessor]): Processors to apply sequentially.
        """
        self.processors = processors
        logging.debug(f"SubtitlePipeline initialized with {len(self.processors)} processors.")

    def execute(self, input_path: str, output_path: str) -> None:
        """
        Reads the file, runs all processors, and writes the output.

        Args:
            input_path (str): Path to the source file.
            output_path (str): Path to save the processed file.
        """
        in_file = Path(input_path)
        out_file = Path(output_path)

        logging.info(f"Starting pipeline execution for file: {input_path}")

        if not in_file.exists():
            error_msg = f"Source file not found: {input_path}"
            logging.error(error_msg)
            raise FileNotFoundError(error_msg)

        # Read
        logging.debug("Reading source file content...")
        content = in_file.read_text(encoding="utf-8")

        # Process sequentially
        for i, processor in enumerate(self.processors, start=1):
            processor_name = processor.__class__.__name__
            logging.info(f"Step {i}/{len(self.processors)}: Running {processor_name}...")
            content = processor.process(content)

        # Write
        logging.debug(f"Writing processed content to {output_path}...")
        out_file.write_text(content, encoding="utf-8")

        logging.info(f"Successfully processed and saved to: {output_path}")