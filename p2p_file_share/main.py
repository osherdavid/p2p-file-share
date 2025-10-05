import logging
import os

import click

from p2p_file_share.client.cli import CLI
from p2p_file_share.client.client import Client
from p2p_file_share.log import setup_logger
from p2p_file_share.server.server import Server

DEFAULT_PORT = 12345

LOG_LEVEL_OPTION = click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False),
    default="INFO",
    help="Set the logging level."
)
PORT_OPTION = click.option("--port", "-p", type=int, default=DEFAULT_PORT, help="The port to listen on.")
HOST_OPTION = click.option("--host", "-h", type=str, required=True, help="The host to connect to.")


@click.group()
def main():
    """Run a simple P2P file sharing application."""
    setup_logger()


@main.command(help="Start a file sharing server.")
@PORT_OPTION
@LOG_LEVEL_OPTION
def start(port: int, log_level: str):
    """Start the file sharing server."""
    print("Starting server...")
    Server(port, getattr(logging, log_level.upper())).start()


@main.command(help="Get a file from a peer.")
@HOST_OPTION
@PORT_OPTION
@click.argument("filename", type=str)
@click.argument("output", required=False, type=str)
@LOG_LEVEL_OPTION
def get(filename:str, output: str, host: str, port: int, log_level: str):
    """Get a file from a peer."""
    output = output or os.path.basename(filename)
    print(f'Starting client to get file "{filename}" from {host}:{port} and save to "{output}"...')
    Client(host, port, getattr(logging, log_level.upper())).execute_command("get", filename, output)


@main.command(help="Upload a file to a peer.")
@HOST_OPTION
@PORT_OPTION
@click.argument("filename", type=str)
@click.argument("destination", required=False, type=str)
@LOG_LEVEL_OPTION
def put(filename:str, destination: str, host: str, port: int, log_level: str):
    """Get a file from a peer."""
    destination = destination or os.path.basename(filename)
    print(f'Starting client to upload a file "{filename}" to {host}:{port} and save to "{destination}"...')
    Client(host, port, getattr(logging, log_level.upper())).execute_command("put", filename, destination)


@main.command(help="Start a shell to interact with a peer.")
@HOST_OPTION
@PORT_OPTION
@LOG_LEVEL_OPTION
def cli(host: str, port: int, log_level: str):
    """Start a shell to interact with a peer."""
    CLI(host, port, getattr(logging, log_level.upper())).start_shell()


if __name__ == "__main__":
    main()
