import os
import socket

import typer

from p2p_file_share.commands.command import Command
from p2p_file_share.commands.commands import register_command
from p2p_file_share.commands.models import FileEntry


@register_command("LST")
class Ls(Command):
    """LS command: List files available on the server."""

    TERMINATION_STRING = b"EOF"

    def execute_server(self, conn: socket.socket, addr):
        """Handle a single client connection in its own thread.

        :param conn: The client socket connection.
        :param addr: The client address.
        """
        self.logger.debug(f"Listing files for {addr}")
        files = os.listdir(".")
        for f in files:
            conn.sendall(FileEntry(filename=f,
                                   filesize=os.path.getsize(f),
                                   is_dir=os.path.isdir(f)
                                   ).pack())
            conn.recv(len(self.ACK_STRING))
        conn.sendall(self.TERMINATION_STRING)

    def execute_client(self, conn: socket.socket):
        """Request the list of files from the server."""
        typer.secho("Files on server:", fg=typer.colors.CYAN, bold=True)
        while (response := conn.recv(self.RECIEVE_BUFFER_SIZE)) != (self.TERMINATION_STRING):
            file_entry = FileEntry.unpack(response)
            typer.secho(f"{file_entry.filename} -- {file_entry.filesize}B",
                         fg=typer.colors.BLUE if file_entry.is_dir else None)
            conn.sendall(self.ACK_STRING)

    @classmethod
    def help(cls) -> str:
        """Return a help string for the command."""
        return "List files available on the server."
