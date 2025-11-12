import logging
from pathlib import Path
from typing import Any, Callable, Tuple, Unpack

from p2p_file_share.client.client import Client


def test_put_uploads_file_to_server(tmp_path: Path,
                                    running_server: Tuple[str, int],
                                    run_with_retry: Callable[[Client, str, Unpack[Any]], Any]):
    """System tests for the entire application.

    Starts a server and tries uploading a file using it.
    Checks that the file was uploaded successfully.

    :param tmp_path: A temporary folder for storing the file uploading.
    :param running_server: A tuple of the host and port of the running server.
    :param run_with_retry: A helper func to run a command with a retry mechanism.
    """
    remote_storage = tmp_path / "remote_storage"
    remote_storage.mkdir()
    client_storage = tmp_path / "client_storage"
    client_storage.mkdir()

    source = client_storage / "upload.txt"
    payload = b"system-test upload payload"
    source.write_bytes(payload)

    destination = remote_storage / "server-upload.txt"

    client = Client(*running_server, logging_level=logging.WARNING)
    run_with_retry(client, "put", str(source), str(destination))

    assert destination.exists()
    assert destination.read_bytes() == payload


def test_get_downloads_file_from_server(tmp_path: Path,
                                        running_server: Tuple[str, int],
                                        run_with_retry: Callable[[Client, str, Unpack[Any]], Any]):
    """System tests for the entire application.

    Starts a server and tries downloading a file from it.
    Checks that the file was downloaded successfully.

    :param tmp_path: A temporary folder for storing the file downloaded.
    :param running_server: A tuple of the host and port of the running server.
    :param run_with_retry: A helper func to run a command with a retry mechanism.
    """
    remote_file = tmp_path / "remote_file.txt"
    contents = b"edge-to-edge download payload"
    remote_file.write_bytes(contents)

    local_target = tmp_path / "downloaded.txt"

    client = Client(*running_server, logging_level=logging.WARNING)
    run_with_retry(client, "get", str(remote_file), str(local_target))

    assert local_target.exists()
    assert local_target.read_bytes() == contents
