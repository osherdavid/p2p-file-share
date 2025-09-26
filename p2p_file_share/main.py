import os
from pathlib import Path

import click

from p2p_file_share.client.client import Client
from p2p_file_share.log import setup_logger
from p2p_file_share.server.server import Server

DEFAULT_PORT = 12345

@click.group()
def main():
    """Run a simple P2P file sharing application."""
    setup_logger()


@main.command(help="Start a file sharing server.")
@click.option("--port", "-p", type=int, default=DEFAULT_PORT, help="The port to listen on.")
def start(port: int):
    """Start the file sharing server."""
    print("Starting server...")
    Server(port).start()


@main.command(help="Get a file from a peer.")
@click.option("--host", "-h", type=str, required=True, help="The host to connect to.")
@click.option("--port", "-p", type=int,  default=DEFAULT_PORT, help="The port to connect to.")
@click.argument("filename", type=str)
@click.argument("output", required=False, type=Path)
def get(filename:str, output: Path, host: str, port: int):
    """Get a file from a peer."""
    output = output if output else Path(os.path.basename(filename))
    print(f'Starting client to get file "{filename}" from {host}:{port} and save to "{output}"...')
    Client(host, port).execute_command("get", filename=filename, output=output)


if __name__ == "__main__":
    main()
