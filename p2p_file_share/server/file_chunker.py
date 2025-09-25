import math
from pathlib import Path


class FileChunker:
    """A utility class to handle file chunking and hashing."""

    def __init__(self, file_path: Path, chunk_size: int = 1024):
        """Initialize the FileChunker with the file path and chunk size.

        :param file_path: The path to the file to be chunked.
        :param chunk_size: The size of each chunk in bytes. Default is 1KB.
        """
        self.file_path = file_path
        self.chunk_size = chunk_size

    def get_chunks(self, start: int = 0):
        """Generate file chunks starting from a specific byte offset.

        :param start: The byte offset to start reading from. Default is 0.
        """
        with self.file_path.open("rb") as f:
            f.seek(start)
            while True:
                chunk = f.read(self.chunk_size)
                if not chunk:
                    break
                yield chunk

    def get_number_of_chunks(self, start: int = 0) -> int:
        """Calculate the number of chunks in the file starting from a specific byte offset.

        :param start: The byte offset to start counting from. Default is 0.
        :return: The number of chunks.
        """
        return math.ceil((self.file_path.stat().st_size - start) / self.chunk_size)
