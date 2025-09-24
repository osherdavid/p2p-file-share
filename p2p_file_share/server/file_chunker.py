import hashlib
import math
import os


class FileChunker:
    """A utility class to handle file chunking and hashing."""

    def __init__(self, file_path: str, chunk_size: int = 1024):
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
        with open(self.file_path, "rb") as f:
            f.seek(start)
            while True:
                chunk = f.read(self.chunk_size)
                if not chunk:
                    break
                yield chunk

    def check_partial_file(self, size: int, file_hash: str) -> bool:
        """Check if the partial file matches the given size and hash.

        :param size: The size of the partial file in bytes.
        :param file_hash: The expected SHA256 hash of the partial file.
        :return: True if the partial file matches the size and hash, False otherwise.
        """
        with open(self.file_path, "rb") as f:
            partial_file_data = f.read(size)
        partial_file_hash = hashlib.sha256(partial_file_data).hexdigest()
        return partial_file_hash == file_hash

    def get_file_hash(self) -> str:
        """Calculate the SHA256 hash of the entire file.

        :return: The SHA256 hash of the file as a hexadecimal string.
        """
        with open(self.file_path, "rb") as f:
            data = f.read()
        return hashlib.sha256(data).hexdigest()

    def get_number_of_chunks(self, start: int = 0) -> int:
        """Calculate the number of chunks in the file starting from a specific byte offset.

        :param start: The byte offset to start counting from. Default is 0.
        :return: The number of chunks.
        """
        return math.ceil((os.path.getsize(self.file_path) - start) / self.chunk_size)
