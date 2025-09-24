import click
from p2p_file_share.server.server import Server
from p2p_file_share.client.client import Client
from p2p_file_share.log import setup_logger

DEFAULT_PORT = 12345

@click.group()
def main():
    setup_logger()


@main.command(help="Start a file sharing server.")
@click.option("--port", "-p", type=int, default=DEFAULT_PORT, help="The port to listen on.")
def start(port: int):
    print(f"Starting server...")
    Server(port).start()


@main.command(help="Get a file from a peer.")
@click.option("--host", "-h", type=str, required=True, help="The host to connect to.")
@click.option("--port", "-p", type=int,  default=DEFAULT_PORT, help="The port to connect to.")
@click.argument("filename", type=str)
def get(filename:str, host: str, port: int):
    print(f'Starting client to get file "{filename}" from {host}:{port}')
    Client(host, port).get(filename)


if __name__ == "__main__":
    main()
