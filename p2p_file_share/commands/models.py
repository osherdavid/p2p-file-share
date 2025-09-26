# mypy: ignore-errors

from cstructpy import GenericStruct
from cstructpy.primitives import BOOL, UINT64, CharArray


class RequestPacket(GenericStruct):
    """Packet sent by the client to request a file from the server."""

    filename: CharArray(128)
    # The file size in bytes.
    # Specified only if the file exists on the host - for continous downloading. 0 if not.
    filesize: UINT64 = 0
    # The SHA256 hash of the file.
    # Specified only if the file exists on the host - for continous downloading. Empty if not.
    filehash: CharArray(64) = ""


class PreTransferPacket(GenericStruct):
    """Packet sent by the server to inform the client about the file status."""

    exists: BOOL # Whether the file exists on the remote.
    continuation: BOOL # Whether this is a continuation of a previous download.
    number_of_chunks: UINT64 = 0 # Number of chunks the file is divided into. 0 if file does not exist.
    filehash: CharArray(64) = "" # The SHA256 hash of the file. Empty if file does not exist.


class FileEntry(GenericStruct):
    """Represents a file entry in the file list."""

    filename: CharArray(128)  # The name of the file.
    filesize: UINT64 # The size of the file in bytes
    is_dir: BOOL # Whether the entry is a directory.
