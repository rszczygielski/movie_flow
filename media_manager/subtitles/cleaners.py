from .base import BaseProcessor

class PolishEncodingFixer(BaseProcessor):
    """
    Processor responsible for fixing broken Polish character encodings.
    """

    # Mapping of broken characters to correct Polish characters
    CHAR_MAP = {
        "ê": "ę", "ñ": "ń", "¹": "ą", "œ": "ś", "¿": "ż",
        "Ÿ": "ź", "³": "ł", "æ": "ć", "¯": "Ż", "Œ": "Ś",
        "£": "Ł", "Ê": "Ę", "Æ": "Ć"
    }

    def process(self, content: str) -> str:
        """
        Replaces corrupted characters with proper Polish letters.

        Args:
            content (str): Subtitles content with potential encoding issues.

        Returns:
            str: Fixed subtitles content.
        """
        for broken_char, correct_char in self.CHAR_MAP.items():
            content = content.replace(broken_char, correct_char)
        return content


class TextSanitizer(BaseProcessor):
    """
    Processor responsible for removing or replacing unwanted special characters.
    """

    def process(self, content: str) -> str:
        """
        Cleans the text from specific unwanted characters like '/'.
        Note: '|' is NOT removed here if we are dealing with MicroDVD,
        as it represents newlines and should be handled by the converter.

        Args:
            content (str): Raw subtitle content.

        Returns:
            str: Sanitized subtitle content.
        """
        # Removing forward slashes
        content = content.replace("/", "")
        return content