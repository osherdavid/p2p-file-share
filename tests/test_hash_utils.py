import hashlib
from pathlib import Path

from p2p_file_share.commands.utils.hash_utils import check_file_integrity, get_file_hash


def test_get_file_hash_matches_sha256(tmp_path: Path) -> None:
    """The helper should mirror hashlib.sha256 output for full files."""
    file_path = tmp_path / "sample.bin"
    data = b"peer-to-peer data payload"
    file_path.write_bytes(data)

    expected = hashlib.sha256(data).hexdigest()
    assert get_file_hash(file_path) == expected


def test_check_file_integrity_detects_matches_and_mismatches(tmp_path: Path) -> None:
    """Integrity helper should validate matching hashes and flag mismatches."""
    file_path = tmp_path / "sample.txt"
    data = b"split data blocks"
    file_path.write_bytes(data)

    full_hash = hashlib.sha256(data).hexdigest()
    mismatched_hash = hashlib.sha256(b"other").hexdigest()

    assert check_file_integrity(file_path, full_hash)
    assert not check_file_integrity(file_path, mismatched_hash)


def test_check_file_integrity_with_offset(tmp_path: Path) -> None:
    """When reading from an offset, only the remaining bytes should be considered."""
    file_path = tmp_path / "sample_offset.txt"
    data = b"abcdefghij"
    file_path.write_bytes(data)

    start = 3
    expected_hash = hashlib.sha256(data[start:]).hexdigest()

    assert check_file_integrity(file_path, expected_hash, start=start)
