import logging
import socket
import threading
import time
from types import SimpleNamespace
from typing import Any, Callable

import pytest

from p2p_file_share.client.client import Client
from p2p_file_share.server.server import Server


HOST = "127.0.0.1"


def _get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((HOST, 0))
        return sock.getsockname()[1]


def _wait_for_server(host: str, port: int, timeout: float = 5.0) -> None:
    """Poll the socket until the server accepts connections."""
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.2) as sock:
                sock.sendall(b"NOP")  # Trigger an immediate ERR response
                sock.recv(3)
                return
        except OSError as exc:
            last_error = exc
            time.sleep(0.05)
    if last_error:
        raise last_error
    raise TimeoutError("Server did not start in time")


def _run_with_retry(client: Client, command: str, *args, timeout: float = 5.0):
    """Retry client commands until the server begins accepting connections."""
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            return client.execute_command(command, *args)
        except ConnectionRefusedError as exc:
            last_error = exc
            time.sleep(0.05)
    if last_error:
        raise last_error
    raise TimeoutError(f"Command '{command}' could not reach the server")


@pytest.fixture(autouse=True)
def disable_tqdm(monkeypatch):
    """Replace progress bars with pass-through iterables for faster, quieter tests."""

    def _passthrough(iterable, *args, **kwargs):
        return iterable

    monkeypatch.setattr("p2p_file_share.commands.put.tqdm", _passthrough)
    monkeypatch.setattr("p2p_file_share.commands.get.tqdm", _passthrough)


@pytest.fixture
def running_server():
    """Spin up a real server instance bound to a free localhost port."""
    port = _get_free_port()
    server = Server(port)
    thread = threading.Thread(target=server.start, daemon=True)
    thread.start()
    try:
        _wait_for_server(HOST, port)
        yield SimpleNamespace(host=HOST, port=port)
    finally:
        server.stop()
        thread.join(timeout=5)


@pytest.fixture
def run_with_retry() -> Callable[[Client, str, Any], Any]:
    """Expose the retry helper to tests via a fixture."""

    def _runner(client: Client, command: str, *args, timeout: float = 5.0):
        return _run_with_retry(client, command, *args, timeout=timeout)

    return _runner
