from p2p_file_share.client.client import Client
from p2p_file_share.commands.commands import print_commands


class CLI:
    """A simple command-line interface (CLI) for interacting with the P2P file sharing server."""

    def __init__(self, host: str, port: int):
        """Initialize the CLI with the server's host and port."""
        self.shell_prompt = f"${host}:{port}> "
        self.client = Client(host, port)

    def start_shell(self):
        """Start the command-line interface shell."""
        while True:
            command_line = input(self.shell_prompt).strip().lower().split()
            if command_line:
                command = command_line[0] if command_line else ""
                arguments = command_line[1:] if len(command_line) > 1 else []
                if command == "help":
                    print("Available commands:")
                    print_commands()
                elif command in ("exit", "quit"):
                    print("Exiting shell.")
                    break
                else:
                    try:
                        self.client.execute_command(command, *arguments)
                    except KeyError:
                        print(f"Unknown command: {command}. Type 'help' for a list of commands.")
                    except Exception as e:
                        print(f"Error executing command '{command}': {e}")
