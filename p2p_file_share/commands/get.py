import os
import socket
import threading
from pathlib import Path

import typer
from tqdm import tqdm

from p2p_file_share.commands.command import Command
from p2p_file_share.commands.commands import register_command
from p2p_file_share.commands.models import PreTransferPacket, RequestPacket
from p2p_file_share.commands.utils.file_chunker import FileChunker
from p2p_file_share.commands.utils.hash_utils import check_file_integrity, get_file_hash


@register_command("GET")
class Get(Command):
    """GET command: Retrieve a file from the server."""

    def execute_server(self, conn: socket.socket, addr):
        """Handle a single client connection in its own thread.

        :param conn: The client socket connection.
        :param addr: The client address.
        """
        with conn:
            self.logger.info(f"Handling connection from {addr} in thread {threading.current_thread().name}")
            request = RequestPacket.unpack(conn.recv(self.RECIEVE_BUFFER_SIZE))
            self.logger.info(f"Received request from {addr}: {request}")
            requested_file = Path(request.filename)
            exists = requested_file.is_file()
            file_chunker = FileChunker(requested_file)
            continueation = (
                request.filesize > 0 and exists and check_file_integrity(requested_file,
                                                                         request.filehash,
                                                                         end=request.filesize)
            )
            start_byte = request.filesize if continueation else 0
            preTransferPacket = PreTransferPacket(
                exists=exists,
                continuation=continueation,
                number_of_chunks=file_chunker.get_number_of_chunks(start=start_byte) if exists else 0,
                filehash=get_file_hash(requested_file) if exists else "",
            )
            conn.sendall(preTransferPacket.pack())
            if not exists:
                self.logger.error(f"File '{requested_file}' does not exist.\
                                    Notifying client and aborting transfer to {addr}.")
                return
            if not continueation and request.filesize > 0:
                self.logger.info("Client requested continuation but no valid partial file found.\
                                  Waiting for client approval.")
                answer = conn.recv(3)  # Wait for client approval (could be improved with a proper message)
                if answer != b"ACK":
                    print(f"Client did not approve continuation. Aborting transfer to {addr}.")
                    return
            self.logger.info(f"Sent pre-transfer packet to {addr}: {preTransferPacket}")
            self.logger.info(f"Starting file transfer to {addr} for file '{requested_file}'")
            for chunk in file_chunker.get_chunks(start=start_byte):
                conn.sendall(chunk)
                conn.recv(3)  # Wait for ACK

    def execute_client(self, conn: socket.socket, filename: str, outputname: str):
        """Request a file from the server.

        :param filename: The name of the file to request.
        """
        output = Path(outputname)
        output = (output / os.path.basename(filename)) if output.is_dir() else output
        self.logger.debug(f'Getting file "{filename}" from {conn} and saving to "{output}"')
        request = RequestPacket(
            filename=filename,
            filesize=output.stat().st_size if output.is_file() else 0,
            filehash=get_file_hash(output) if output.is_file() else "",
        )
        conn.sendall(request.pack())
        preTransferPacket = PreTransferPacket.unpack(conn.recv(4096))
        self.logger.debug(f"Received pre-transfer packet: {preTransferPacket}")
        if preTransferPacket.exists:
            if request.filesize > 0 and not preTransferPacket.continuation:
                if typer.confirm("The local file does not match the server's file. Overwrite?", default=True):
                    typer.secho(f"Overwriting {output}.", fg=typer.colors.YELLOW)
                    conn.sendall(b"ACK")
                    self._download_file(output, preTransferPacket, conn)
                    return
                else:
                    typer.secho(f'Aborting download of "{output}".', fg=typer.colors.RED)
                    return
            elif preTransferPacket.continuation:
                typer.secho(f'Continuing download of "{output}".', fg=typer.colors.YELLOW)
            self._download_file(output, preTransferPacket, conn)
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

    @classmethod
    def help(cls) -> str:
        """Help message for the GET command."""
        return "get command: Retrieve a file from the server. Usage: get <filename>"
