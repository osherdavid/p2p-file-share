import os

import typer

from p2p_file_share.commands.command import Command
from p2p_file_share.commands.commands import register_command


@register_command("PWD")
class Pwd(Command):
    """Print current working directory of the server."""

    def execute_server(self, conn, addr, *args, **kwargs):
        """Send back the current working directory."""
        conn.sendall(os.getcwd().encode())

    def execute_client(self, conn, *args, **kwargs):
        """Request the server to send its current working directory."""
        response = conn.recv(self.RECIEVE_BUFFER_SIZE)
        typer.secho("Server current working directory:", bold=True)
        typer.secho(response.decode())

    @classmethod
    def help(cls) -> str:
        """Return a help string for the command."""
        return "The current working directory of the server"
