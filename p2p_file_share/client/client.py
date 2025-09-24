import hashlib
import os
import socket

import typer
from tqdm import tqdm

from p2p_file_share.common.models import PreTransferPacket, RequestPacket
from p2p_file_share.log import setup_logger


class Client:
    """The client class responsible for requesting files from the server."""

    def __init__(self, host: str, port: int):
        """Initialize the client with the server's host and port.

        :param host: The server's hostname or IP address.
        :param port: The server's port number.
        """
        self.logger = setup_logger("Client")
        self.host = host
        self.port = port

    def get(self, filename: str, output_filename: str):
        """Request a file from the server.

        :param filename: The name of the file to request.
        """
        output_filename = os.path.abspath(os.path.join(output_filename, os.path.basename(filename))
                                           if os.path.isdir(output_filename)
                                           else output_filename)

        self.logger.debug(f'Getting file "{filename}" from {self.host}:{self.port} and saving to "{output_filename}"')
        request = RequestPacket(
            filename=filename,
            filesize=os.path.getsize(output_filename) if os.path.isfile(output_filename) else 0,
            filehash=self.get_file_hash(output_filename) if os.path.isfile(output_filename) else "",
        )

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            s.sendall(request.to_bytes())
            preTransferPacket = PreTransferPacket.from_bytes(s.recv(4096))
            self.logger.debug(f"Received pre-transfer packet: {preTransferPacket}")
            if preTransferPacket.exists:
                if request.filesize > 0 and not preTransferPacket.continuation:
                    if typer.confirm("The local file does not match the server's file. Overwrite?", default=True):
                        typer.secho(f"Overwriting {output_filename}.", fg=typer.colors.YELLOW)
                        s.sendall(b"ACK")
                        self._download_file(output_filename, request, preTransferPacket, s)
                        return
                    else:
                        typer.secho(f'Aborting download of "{output_filename}".', fg=typer.colors.RED)
                        return
                elif preTransferPacket.continuation:
                    typer.secho(f'Continuing download of "{output_filename}".', fg=typer.colors.YELLOW)
                self._download_file(output_filename, request, preTransferPacket, s)
            else:
                typer.secho(f'File "{filename}" does not exist on the server.', fg=typer.colors.RED)

    def _download_file(self, output_filename: str,
                       request: RequestPacket,
                       preTransferPacket: PreTransferPacket,
                       sock: socket.socket):
        """Download the file from the server.

        :param request: The original request packet.
        :param preTransferPacket: The pre-transfer packet received from the server.
        :param sock: The connected socket to the server.
        """
        with open(output_filename, "ab" if preTransferPacket.continuation else "wb") as f:
            for _ in tqdm(range(preTransferPacket.number_of_chunks)):
                chunk = sock.recv(4096)
                f.write(chunk)
                sock.sendall(b"ACK")  # Send acknowledgment for each chunk
        if self.check_file_integrity(request.filename, preTransferPacket.filehash):
            typer.secho(f'File "{request.filename}" downloaded successfully.', fg=typer.colors.GREEN)
        else:
            typer.secho(f'File "{request.filename}" downloaded but failed integrity check!', fg=typer.colors.RED)

    @staticmethod
    def check_file_integrity(filename: str, expected_hash: str):
        """Check the integrity of the downloaded file by comparing its hash to the expected hash.

        :param filename: The name of the file to check.
        :param expected_hash: The expected SHA256 hash of the file.
        :return: True if the file's hash matches the expected hash, False otherwise.
        """
        return expected_hash == Client.get_file_hash(filename)

    @staticmethod
    def get_file_hash(filename: str) -> str:
        """Calculate the SHA256 hash of a file.

        :param filename: The name of the file to hash.
        :return: The SHA256 hash of the file as a hexadecimal string.
        """
        with open(filename, "rb") as f:
            data = f.read()
        return hashlib.sha256(data).hexdigest()
