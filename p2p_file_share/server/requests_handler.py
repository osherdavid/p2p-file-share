import socket
import threading
from pathlib import Path

from p2p_file_share.common.hash_utils import check_file_integrity, get_file_hash
from p2p_file_share.common.models import PreTransferPacket, RequestPacket
from p2p_file_share.log import setup_logger
from p2p_file_share.server.file_chunker import FileChunker


class RequestsHandler:
    """Handles incoming file requests from clients."""

    def __init__(self):
        """Initialize the request handler."""
        self.logger = setup_logger("RequestsHandler")
        self.RECIEVE_BUFFER_SIZE = 4096

    def handle_client_download(self, conn: socket.socket, addr):
        """Handle a single client connection in its own thread.

        :param conn: The client socket connection.
        :param addr: The client address.
        """
        with conn:
            self.logger.info(f"Handling connection from {addr} in thread {threading.current_thread().name}")
            request = RequestPacket.unpack(conn.recv(self.RECIEVE_BUFFER_SIZE))
            self.logger.info(f"Received request from {addr}: {request}")
            requested_file = Path(request.filename)
            exists = requested_file.is_file()
            file_chunker = FileChunker(requested_file)
            continueation = (
                request.filesize > 0 and exists and check_file_integrity(requested_file,
                                                                         request.filehash,
                                                                         end=request.filesize)
            )
            start_byte = request.filesize if continueation else 0
            preTransferPacket = PreTransferPacket(
                exists=exists,
                continuation=continueation,
                number_of_chunks=file_chunker.get_number_of_chunks(start=start_byte) if exists else 0,
                filehash=get_file_hash(requested_file) if exists else 0,
            )
            conn.sendall(preTransferPacket.pack())
            if not exists:
                self.logger.error(f"File '{requested_file}' does not exist.\
                                    Notifying client and aborting transfer to {addr}.")
                return
            if not continueation and request.filesize > 0:
                self.logger.info("Client requested continuation but no valid partial file found.\
                                  Waiting for client approval.")
                answer = conn.recv(3)  # Wait for client approval (could be improved with a proper message)
                if answer != b"ACK":
                    print(f"Client did not approve continuation. Aborting transfer to {addr}.")
                    return
            self.logger.info(f"Sent pre-transfer packet to {addr}: {preTransferPacket}")
            self.logger.info(f"Starting file transfer to {addr} for file '{requested_file}'")
            for chunk in file_chunker.get_chunks(start=start_byte):
                conn.sendall(chunk)
                conn.recv(3)  # Wait for ACK
