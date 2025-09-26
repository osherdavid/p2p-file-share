import os
import socket
from pathlib import Path
from typing import Generator, Optional

import typer
from tqdm import tqdm

from p2p_file_share.commands.command import Command
from p2p_file_share.commands.commands import register_command
from p2p_file_share.commands.models import PreTransferPacket, RequestPacket
from p2p_file_share.commands.utils.file_chunker import FileChunker
from p2p_file_share.commands.utils.hash_utils import check_file_integrity, get_file_hash


@register_command("PUT")
class Put(Command):
    """Upload a file to a server."""

    def execute_server(self, conn: socket.socket, addr):
        """Recieve a file upload from a client."""
        upload_destination = Path(conn.recv(self.RECIEVE_BUFFER_SIZE).decode())
        lock_file = self._validate_upload(addr, upload_destination)
        if not lock_file:
            conn.sendall(self.ERR_STRING)
            return
        try:
            request = RequestPacket(
                filename=str(upload_destination),
                filesize=upload_destination.stat().st_size if upload_destination.is_file() else 0,
                filehash=get_file_hash(upload_destination) if upload_destination.is_file() else "",
            )
            self.logger.info(f"Sending a request packet: {request}")
            conn.sendall(request.pack())
            pre_transfer_packet = PreTransferPacket.unpack(conn.recv(self.RECIEVE_BUFFER_SIZE))
            self.logger.info(f"Got a pre-transfer packet: {pre_transfer_packet}")
            self._recieve_upload(conn, upload_destination, pre_transfer_packet)
        finally:
            os.remove(lock_file)

    def execute_client(self, conn: socket.socket, filename: str, destination: str):
        """Upload a file to the server."""
        file_path = Path(filename)
        if not file_path.is_file():
            typer.secho(f"{file_path} is not a file.", fg=typer.colors.RED)
            return
        conn.sendall(destination.encode())
        response = conn.recv(self.RECIEVE_BUFFER_SIZE)
        if response == self.ERR_STRING:
            typer.secho("The server did not authorize the upload.", fg=typer.colors.RED)
            return
        response = RequestPacket.unpack(response)
        continueation = (
            response.filesize > 0 and check_file_integrity(file_path,
                                                           response.filehash,
                                                           end=response.filesize)
        )
        start_byte = response.filesize if continueation else 0
        file_chunker = FileChunker(file_path)
        pre_transfer_packet = PreTransferPacket(
            exists=True,
            continuation=continueation,
            number_of_chunks=file_chunker.get_number_of_chunks(start=start_byte),
            filehash=get_file_hash(file_path),
        )
        conn.sendall(pre_transfer_packet.pack())
        if continueation:
            typer.secho("Continueing an older uplaod...", fg=typer.colors.GREEN)
        self._upload_file(conn, file_chunker.get_chunks(start=start_byte))

    def _upload_file(self,
                    conn: socket.socket,
                    chunks: Generator) -> None:
        """Upload the file from the server.

        :param conn: The connected socket to the server.
        :param chunks: The generator created by the file chuker that generated the chunks to send.
        """
        for chunk in tqdm(list(chunks)):
            conn.sendall(chunk)
            conn.recv(len(self.ACK_STRING))
        hash_result = conn.recv(len(self.ACK_STRING))
        if hash_result == self.ACK_STRING:
            typer.secho("File uploaded successfully.", fg=typer.colors.GREEN)
        else:
            typer.secho("File uploaded but failed integrity check!", fg=typer.colors.RED)

    def _validate_upload(self, addr, upload_destination: Path) -> Optional[Path]:
        """Validate if the upload can proceed as requested.

        :param upload_destination: The path requested to upload to.
        :param lock_file: The lock file that will used by that path.
        :return: The lock file of that path if the upload can proceed, None if not.
        """
        if not upload_destination:
            self.logger.error("Didn't get any upload destination")
            return None
        self.logger.info(f"Got a request to upload a file to {upload_destination} by {addr}")
        if upload_destination.is_dir():
            self.logger.error(f"Couldn't upload a file to {upload_destination} becuase its a directory.")
            return None
        # Create the lock file.
        lock_file = upload_destination.with_name(f".{upload_destination.name}.lock")
        try:
            lock_file.touch(exist_ok=False)
        except Exception as e:
            self.logger.error(f"Couldn't upload a file to {upload_destination} \
                              becuase couldn't create the lock file: {e}")
            return None
        return lock_file

    def _recieve_upload(self, conn, upload_destination: Path, pre_transfer_packet: PreTransferPacket) -> None:
        """Recieve the upload from the client."""
        if pre_transfer_packet.continuation:
            self.logger.info("Continueing an older upload...")
        with open(upload_destination, "ab" if pre_transfer_packet.continuation else "wb") as f:
            for _ in range(pre_transfer_packet.number_of_chunks):
                f.write(conn.recv(self.RECIEVE_BUFFER_SIZE))
                conn.send(self.ACK_STRING)
        conn.send(self.ACK_STRING
                    if check_file_integrity(upload_destination, pre_transfer_packet.filehash)
                    else self.ERR_STRING)

    @classmethod
    def help(cls) -> str:
        """Help message for the GET command."""
        return "Upload a file to the server. Usage: put <filename> <destination>"
