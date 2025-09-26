import os

import typer

from p2p_file_share.commands.command import Command
from p2p_file_share.commands.commands import register_command


@register_command("CWD")
class Cd(Command):
    """Change the current working directory of the server."""

    def execute_server(self, conn, addr, *args, **kwargs):
        """Handle request to change the current working directory."""
        requested_directory = conn.recv(self.RECIEVE_BUFFER_SIZE)
        self.logger.info(f"Requested to change directory to: {requested_directory} by {addr}")
        try:
            os.chdir(requested_directory)
            conn.sendall(self.ACK_STRING)
        except Exception as e:
            self.logger.error(f"Couldn't change working directory because: {e}")
            conn.sendall(self.ERR_STRING)


    def execute_client(self, conn, directory: str, *args, **kwargs):
        """Send and handle repsponse for the request to change the working directory."""
        conn.sendall(directory.encode())
        response = conn.recv(self.RECIEVE_BUFFER_SIZE)
        if response == self.ACK_STRING:
            typer.secho(f"Server successfuly changed its current working directory to {directory}.",
                        fg=typer.colors.GREEN)
        else:
            typer.secho(f"Server could not change its working directory to {directory}.",
                        fg=typer.colors.GREEN)

    @classmethod
    def help(cls) -> str:
        """Return a help string for the command."""
        return "Request the server to change its current working directory."
