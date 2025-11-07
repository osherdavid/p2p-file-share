from p2p_file_share.commands.utils.file_chunker import FileChunker


def test_get_chunks_splits_file_by_chunk_size(tmp_path):
    """Chunk generator should yield sequential slices that reconstruct the file."""
    file_path = tmp_path / "chunked.bin"
    content = b"0123456789ABCDEF"
    file_path.write_bytes(content)

    chunker = FileChunker(file_path, chunk_size=4)
    chunks = list(chunker.get_chunks())

    assert b"".join(chunks) == content
    assert chunks == [content[i:i + 4] for i in range(0, len(content), 4)]


def test_get_chunks_can_start_from_offset(tmp_path):
    """Chunk iteration should respect non-zero starting offsets."""
    file_path = tmp_path / "offset.bin"
    content = b"abcdefghij"
    file_path.write_bytes(content)

    chunker = FileChunker(file_path, chunk_size=3)
    start = 4
    chunks = list(chunker.get_chunks(start=start))

    assert b"".join(chunks) == content[start:]


def test_get_number_of_chunks_accounts_for_remainder(tmp_path):
    """Number of chunks should round up when the file size is not divisible by chunk size."""
    file_path = tmp_path / "count.bin"
    content = b"x" * 2500
    file_path.write_bytes(content)

    chunker = FileChunker(file_path, chunk_size=1024)

    assert chunker.get_number_of_chunks() == 3
    assert chunker.get_number_of_chunks(start=1024) == 2
    assert chunker.get_number_of_chunks(start=2500) == 0
