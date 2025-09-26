from abc import ABC, abstractmethod

from p2p_file_share.log import setup_logger


class Command(ABC):
    """Abstract base class for command handlers."""

    RECIEVE_BUFFER_SIZE = 4096  # 4KB

    def __init__(self):
        """Initialize the command with a logger."""
        self.logger = setup_logger(self.__class__.__name__)

    @abstractmethod
    def execute_server(self, conn, addr, *args, **kwargs):
        """Handle a single client connection."""
        pass

    @abstractmethod
    def execute_client(self, conn, *args, **kwargs):
        """Execute the command from the client side."""
        pass

    @classmethod
    def help(cls) -> str:
        """Return a help string for the command."""
        return "No help available for this command."
