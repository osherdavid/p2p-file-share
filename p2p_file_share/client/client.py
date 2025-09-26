import socket

from p2p_file_share.commands.commands import NAME_TO_CODE, get_command
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

    def execute_command(self, command_name: str, *args, **kwargs):
        """Execute a command by name.

        :param command_name: The name of the command to execute.
        :param args: Positional arguments to pass to the command.
        :param kwargs: Keyword arguments to pass to the command.
        """
        self.logger.info(f"Executing command '{command_name}' with args {args} and kwargs {kwargs}")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conn:
            conn.connect((self.host, self.port))
            conn.sendall(NAME_TO_CODE[command_name].encode())
            command = get_command(name=command_name)
            command.execute_client(conn, *args, **kwargs)
