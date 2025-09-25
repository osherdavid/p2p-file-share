import hashlib
from pathlib import Path


def get_file_hash(path: Path) -> str:
    """Calculate the SHA256 hash of the entire file.

    :return: The SHA256 hash of the file as a hexadecimal string.
    """
    with path.open("rb") as f:
        data = f.read()
    return hashlib.sha256(data).hexdigest()


def check_file_integrity(path: Path, file_hash: str, start=0, end=None) -> bool:
    """Check the integrity of a file by comparing its hash to the expected hash.

    :param file_hash: The expected SHA256 hash of the file.
    :param start: The byte offset to start reading from. Default is 0.
    :param end: The byte offset to stop reading at. Default is None (read to end of file).
    :return: True if the file's hash matches the expected hash, False otherwise.
    """
    with path.open("rb") as f:
        f.seek(start)
        partial_file_data = f.read(end)
    partial_file_hash = hashlib.sha256(partial_file_data).hexdigest()
    return partial_file_hash == file_hash
