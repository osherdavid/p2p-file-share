import logging
from pathlib import Path

from p2p_file_share.client.client import Client


def test_put_uploads_file_to_server(tmp_path: Path, running_server, run_with_retry):
    remote_storage = tmp_path / "remote_storage"
    remote_storage.mkdir()
    client_storage = tmp_path / "client_storage"
    client_storage.mkdir()

    source = client_storage / "upload.txt"
    payload = b"system-test upload payload"
    source.write_bytes(payload)

    destination = remote_storage / "server-upload.txt"

    client = Client(running_server.host, running_server.port, logging_level=logging.WARNING)
    run_with_retry(client, "put", str(source), str(destination))

    assert destination.exists()
    assert destination.read_bytes() == payload


def test_get_downloads_file_from_server(tmp_path: Path, running_server, run_with_retry):
    remote_file = tmp_path / "remote_file.txt"
    contents = b"edge-to-edge download payload"
    remote_file.write_bytes(contents)

    local_target = tmp_path / "downloaded.txt"

    client = Client(running_server.host, running_server.port, logging_level=logging.WARNING)
    run_with_retry(client, "get", str(remote_file), str(local_target))

    assert local_target.exists()
    assert local_target.read_bytes() == contents
