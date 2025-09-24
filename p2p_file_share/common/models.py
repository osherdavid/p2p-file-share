from __future__ import annotations

import struct
from typing import ClassVar

from pydantic import BaseModel


class RequestPacket(BaseModel):
    """Packet sent by the client to request a file from the server."""

    filename: str
    # The file size in bytes.
    # Specified only if the file exists on the host - for continous downloading. 0 if not.
    filesize: int = 0
    # The SHA256 hash of the file.
    # Specified only if the file exists on the host - for continous downloading.. Empty if not.
    filehash: str = ""

    FORMAT: ClassVar = "128sQ64s"  # 128-byte filename, 8-byte filesize, 64-byte filehash

    def to_bytes(self) -> bytes:
        """Convert the RequestPacket to bytes for transmission."""
        return struct.pack(self.FORMAT,
                           self.filename.encode(),
                           self.filesize, self.filehash.encode())

    @classmethod
    def from_bytes(cls, data: bytes) -> RequestPacket:
        """Create a RequestPacket from bytes received."""
        filename, filesize, filehash = struct.unpack(RequestPacket.FORMAT, data)
        return RequestPacket(
            filename=filename.decode().rstrip("\x00"),
            filesize=filesize,
            filehash=filehash.decode().rstrip("\x00")
        )


class PreTransferPacket(BaseModel):
    """Packet sent by the server to inform the client about the file status."""

    exists: bool # Whether the file exists on the remote.
    continuation: bool # Whether this is a continuation of a previous download.
    number_of_chunks: int = 0 # Number of chunks the file is divided into. 0 if file does not exist.
    filehash: str = "" # The SHA256 hash of the file. Empty if file does not exist.

    # 1-byte bool exists, 1-byte bool continuation, 8-byte number_of_chunks, 64-byte filehash
    FORMAT: ClassVar = "??Q64s"

    def to_bytes(self) -> bytes:
        """Convert the PreTransferPacket to bytes for transmission."""
        return struct.pack(self.FORMAT,
                           self.exists,
                           self.continuation,
                           self.number_of_chunks,
                           self.filehash.encode())

    @classmethod
    def from_bytes(cls, data: bytes) -> PreTransferPacket:
        """Create a PreTransferPacket from bytes received."""
        exists, continuation, number_of_chunks, filehash = struct.unpack(PreTransferPacket.FORMAT, data)
        return PreTransferPacket(
            exists=exists,
            continuation=continuation,
            number_of_chunks=number_of_chunks,
            filehash=filehash.decode().rstrip("\x00")
        )
