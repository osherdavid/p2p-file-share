import os
import signal
import socket
import threading

from p2p_file_share.log import setup_logger
from p2p_file_share.common.models import PreTransferPacket, RequestPacket
from p2p_file_share.server.file_chunker import FileChunker


class Server:
    """The server class responsible for handling file sharing requests."""

    HOST: str = "0.0.0.0"  # Listen on all interfaces
    RECIEVE_BUFFER_SIZE: int = 4096  # 4KB

    def __init__(self, port: int):
        """Initialize the server with the specified port.

        :param port: The port number to listen on.
        """
        self.logger = setup_logger("Server")
        self.port = port
        self._should_run = threading.Event()
        self._should_run.set()
        self._sock = None  # type: socket.socket | None
        self._register_signal_handlers()

    def start(self):
        """Start the server: bind, listen, and accept connections."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Store the socket so stop() can close it from the signal handler
            self._sock = s
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.HOST, self.port))
            s.listen()
            s.settimeout(1.0)  # Use a short timeout on accept() to check _should_run flag
            self.logger.info(f"Server started on port {self.port}")

            try:
                while self._should_run.is_set():
                    try:
                        conn, addr = s.accept()
                    except socket.timeout:
                        # Timeout is expected; loop back and check _should_run
                        continue
                    self.logger.info(f"Accepted connection from {addr}")
                    # Spawn a thread to handle the client
                    t = threading.Thread(target=self._handle_client, args=(conn, addr), daemon=True)
                    t.start()
            finally:
                self._should_run.clear()
                self.logger.info("Server stopped")

    def stop(self):
        """Stop the server: clear run flag and close the listening socket to unblock accept()."""
        self.logger.info("Server stop requested")
        self._should_run.clear()
        if self._sock:
            try:
                # Closing the listening socket will cause accept() to raise and the loop to exit
                self._sock.close()
            except Exception:
                pass

    def _handle_client(self, conn: socket.socket, addr):
        """Handle a single client connection in its own thread.

        :param conn: The client socket connection.
        :param addr: The client address.
        """
        with conn:
            self.logger.info(f"Handling connection from {addr} in thread {threading.current_thread().name}")
            request = RequestPacket.from_bytes(conn.recv(self.RECIEVE_BUFFER_SIZE))
            self.logger.info(f"Received request from {addr}: {request}")
            exists = os.path.isfile(request.filename)
            file_chunker = FileChunker(request.filename)
            continueation = (
                request.filesize > 0 and exists and file_chunker.check_partial_file(request.filesize, request.filehash)
            )
            start_byte = request.filesize if continueation else 0
            preTransferPacket = PreTransferPacket(
                exists=exists,
                continuation=continueation,
                number_of_chunks=file_chunker.get_number_of_chunks(start=start_byte) if exists else 0,
                filehash=file_chunker.get_file_hash() if exists else "",
            )
            conn.sendall(preTransferPacket.to_bytes())
            if not exists:
                self.logger.error(f"File '{request.filename}' does not exist. Notifying client and aborting transfer to {addr}.")
                return
            if not continueation and request.filesize > 0:
                self.logger.info("Client requested continuation but no valid partial file found. Waiting for client approval.")
                answer = conn.recv(3)  # Wait for client approval (could be improved with a proper message)
                if answer != b"ACK":
                    print(f"Client did not approve continuation. Aborting transfer to {addr}.")
                    return
            self.logger.info(f"Sent pre-transfer packet to {addr}: {preTransferPacket}")
            self.logger.info(f"Starting file transfer to {addr} for file '{request.filename}'")
            for chunk in file_chunker.get_chunks(start=start_byte):
                conn.sendall(chunk)
                import time

                time.sleep(0.1)  # Throttle to avoid overwhelming the client
                conn.recv(3)  # Wait for ACK

    def _sigint_handler(self, sig, frame):
        """Signal handler that delegates to stop().

        :param sig: The signal number.
        :param frame: The current stack frame.
        """
        print("SIGINT received, stopping server...")
        try:
            self.stop()
        except Exception as e:
            self.logger.error(f"Error while stopping server from signal handler: {e}")

    def _register_signal_handlers(self):
        """Register signal handlers for SIGINT and SIGTERM to stop the server."""
        try:
            signal.signal(signal.SIGINT, self._sigint_handler)
            # SIGTERM may not exist on Windows but register when available
            try:
                signal.signal(signal.SIGTERM, self._sigint_handler)
            except AttributeError:
                pass
            self.logger.info("Signal handlers registered for SIGINT/SIGTERM")
        except Exception as e:
            # Signal registration may fail on some platforms or non-main threads, acknowledge it and continue
            self.logger.error(f"Could not register signal handlers: {e}")
