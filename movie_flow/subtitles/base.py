from abc import ABC, abstractmethod

class BaseProcessor(ABC):
    """
    Abstract base class for all subtitle processors.
    """

    @abstractmethod
    def process(self, content: str) -> str:
        """
        Processes the subtitle content.

        Args:
            content (str): The raw content of the subtitle file.

        Returns:
            str: The processed subtitle content.
        """
        pass