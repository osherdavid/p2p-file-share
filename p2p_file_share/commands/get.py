import os
import socket
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
    """Retrieve a file from the server."""

    def execute_server(self, conn: socket.socket, addr):
        """Handle a single client connection in its own thread."""
        request = RequestPacket.unpack(conn.recv(self.RECIEVE_BUFFER_SIZE))
        self.logger.info(f"Received request from {addr}: {request}")
        file_chunker = FileChunker(Path(request.filename))
        pre_transfer_packet = self._prepare_pre_transfer_packet(request, file_chunker)
        self.logger.info(f"Sent pre-transfer packet to {addr}: {pre_transfer_packet}")
        conn.sendall(pre_transfer_packet.pack())
        if self._validate_transfer(conn, addr, request, pre_transfer_packet):
            self._send_file(conn, addr, request, pre_transfer_packet, file_chunker)

    def _validate_transfer(self, conn, addr, request: RequestPacket, pre_transfer_packet: PreTransferPacket) -> bool:
        if not pre_transfer_packet.exists:
            self.logger.error(f"File '{request.filename}' does not exist.\
                                Notifying client and aborting transfer to {addr}.")
            return False
        if not pre_transfer_packet.continuation and request.filesize > 0:
            self.logger.info("Client requested continuation but no valid partial file found.\
                                Waiting for client approval.")
            answer = conn.recv(len(self.ACK_STRING))
            if answer != self.ACK_STRING:
                print(f"Client did not approve continuation. Aborting transfer to {addr}.")
                return False
        return True

    def _send_file(self, conn, addr, request, pre_transfer_packet, file_chunker):
        self.logger.info(f"Starting file transfer to {addr} for file '{request.filename}'")
        for chunk in file_chunker.get_chunks(start=request.filesize if pre_transfer_packet.continuation else 0):
            conn.sendall(chunk)
            conn.recv(len(self.ACK_STRING))  # Wait for ACK

    def _prepare_pre_transfer_packet(self, request: RequestPacket, file_chunker: FileChunker) -> PreTransferPacket:
        requested_file = Path(request.filename)
        exists = requested_file.is_file()
        continueation = (
            request.filesize > 0 and exists and check_file_integrity(requested_file,
                                                                        request.filehash,
                                                                        end=request.filesize)
        )
        start_byte = request.filesize if continueation else 0
        return PreTransferPacket(
            exists=exists,
            continuation=continueation,
            number_of_chunks=file_chunker.get_number_of_chunks(start=start_byte) if exists else 0,
            filehash=get_file_hash(requested_file) if exists else "",
        )

    def execute_client(self, conn: socket.socket, filename: str, outputname: str):
        """Request a file from the server."""
        output = Path(outputname)
        output = (output / os.path.basename(filename)) if output.is_dir() else output
        self.logger.debug(f'Getting file "{filename}" from {conn} and saving to "{output}"')
        request = RequestPacket(
            filename=filename,
            filesize=output.stat().st_size if output.is_file() else 0,
            filehash=get_file_hash(output) if output.is_file() else "",
        )
        conn.sendall(request.pack())
        pre_transter_packet = PreTransferPacket.unpack(conn.recv(4096))
        self.logger.debug(f"Received pre-transfer packet: {pre_transter_packet}")
        if pre_transter_packet.exists:
            if request.filesize > 0 and not pre_transter_packet.continuation:
                if typer.confirm("The local file does not match the server's file. Overwrite?", default=True):
                    typer.secho(f"Overwriting {output}.", fg=typer.colors.YELLOW)
                    conn.sendall(self.ACK_STRING)
                    self._download_file(output, pre_transter_packet, conn)
                    return
                else:
                    typer.secho(f'Aborting download of "{output}".', fg=typer.colors.RED)
                    return
            elif pre_transter_packet.continuation:
                typer.secho(f'Continuing download of "{output}".', fg=typer.colors.YELLOW)
            self._download_file(output, pre_transter_packet, conn)
        else:
            typer.secho(f'File "{filename}" does not exist on the server.', fg=typer.colors.RED)

    def _download_file(self,
                       output: Path,
                       pre_transter_packet: PreTransferPacket,
                       sock: socket.socket):
        """Download the file from the server.

        :param request: The original request packet.
        :param pre_transter_packet: The pre-transfer packet received from the server.
        :param sock: The connected socket to the server.
        """
        with output.open("ab" if pre_transter_packet.continuation else "wb") as f:
            for _ in tqdm(range(pre_transter_packet.number_of_chunks)):
                chunk = sock.recv(4096)
                f.write(chunk)
                sock.sendall(self.ACK_STRING)  # Send acknowledgment for each chunk
        if check_file_integrity(output, pre_transter_packet.filehash):
            typer.secho(f'File "{output}" downloaded successfully.', fg=typer.colors.GREEN)
        else:
            typer.secho(f'File "{output}" downloaded but failed integrity check!', fg=typer.colors.RED)

    @classmethod
    def help(cls) -> str:
        """Help message for the GET command."""
        return "Retrieve a file from the server. Usage: get <remote_filename> <local_filename>"
