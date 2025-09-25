import os
import socket
from pathlib import Path

import typer
from tqdm import tqdm

from p2p_file_share.common.hash_utils import check_file_integrity, get_file_hash
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

    def get(self, filename: str, output: Path):
        """Request a file from the server.

        :param filename: The name of the file to request.
        """
        output = (output / os.path.basename(filename)) if output.is_dir() else output

        self.logger.debug(f'Getting file "{filename}" from {self.host}:{self.port} and saving to "{output}"')
        request = RequestPacket(
            filename=filename,
            filesize=output.stat().st_size if output.is_file() else 0,
            filehash=get_file_hash(output) if output.is_file() else "",
        )

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            s.sendall(request.pack())
            preTransferPacket = PreTransferPacket.unpack(s.recv(4096))
            self.logger.debug(f"Received pre-transfer packet: {preTransferPacket}")
            if preTransferPacket.exists:
                if request.filesize > 0 and not preTransferPacket.continuation:
                    if typer.confirm("The local file does not match the server's file. Overwrite?", default=True):
                        typer.secho(f"Overwriting {output}.", fg=typer.colors.YELLOW)
                        s.sendall(b"ACK")
                        self._download_file(output, preTransferPacket, s)
                        return
                    else:
                        typer.secho(f'Aborting download of "{output}".', fg=typer.colors.RED)
                        return
                elif preTransferPacket.continuation:
                    typer.secho(f'Continuing download of "{output}".', fg=typer.colors.YELLOW)
                self._download_file(output, preTransferPacket, s)
            else:
                typer.secho(f'File "{filename}" does not exist on the server.', fg=typer.colors.RED)

    def _download_file(self,
                       output: Path,
                       preTransferPacket: PreTransferPacket,
                       sock: socket.socket):
        """Download the file from the server.

        :param request: The original request packet.
        :param preTransferPacket: The pre-transfer packet received from the server.
        :param sock: The connected socket to the server.
        """
        with output.open("ab" if preTransferPacket.continuation else "wb") as f:
            for _ in tqdm(range(preTransferPacket.number_of_chunks)):
                chunk = sock.recv(4096)
                f.write(chunk)
                sock.sendall(b"ACK")  # Send acknowledgment for each chunk
        if check_file_integrity(output, preTransferPacket.filehash):
            typer.secho(f'File "{output}" downloaded successfully.', fg=typer.colors.GREEN)
        else:
            typer.secho(f'File "{output}" downloaded but failed integrity check!', fg=typer.colors.RED)
