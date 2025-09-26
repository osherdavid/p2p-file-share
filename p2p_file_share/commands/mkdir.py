import os

import typer

from p2p_file_share.commands.command import Command
from p2p_file_share.commands.commands import register_command


@register_command("MKD")
class Mkdir(Command):
    """Create a new directory on the  server."""

    def execute_server(self, conn, addr, *args, **kwargs):
        """Handle request to create a new directory."""
        requested_directory = conn.recv(self.RECIEVE_BUFFER_SIZE)
        self.logger.info(f"Requested to create the directory: {requested_directory} by {addr}")
        try:
            os.mkdir(requested_directory)
            conn.sendall(self.ACK_STRING)
        except Exception as e:
            self.logger.error(f"Couldn't create the directory because: {e}")
            conn.sendall(self.ERR_STRING)

    def execute_client(self, conn, directory: str, *args, **kwargs):
        """Send and handle repsponse for the request to create the directory."""
        conn.sendall(directory.encode())
        response = conn.recv(self.RECIEVE_BUFFER_SIZE)
        if response == self.ACK_STRING:
            typer.secho(f"Server successfuly created the directory {directory}.",
                        fg=typer.colors.GREEN)
        else:
            typer.secho(f"Server could not create the directory {directory}.",
                        fg=typer.colors.RED)

    @classmethod
    def help(cls) -> str:
        """Return a help string for the command."""
        return "Create a new directory on the remote server."
