import asyncio
import socket
import base64
from uuid import uuid4
from typing import Callable
from message import Message, MessageType


class Server:
    host: str
    port: int
    _get_input: Callable[[], str]
    _put_output: Callable[[str], None]
    server_socket: socket.socket
    client_connections: dict[str, asyncio.StreamWriter]
    running: bool
    lock: asyncio.Lock

    def __init__(
        self,
        input_callback: Callable[[], str],
        output_callback: Callable[[str], None],
        host: str = "0.0.0.0",
        port: int = 8080,
    ):
        self._get_input = input_callback
        self._put_output = output_callback
        self.host = host
        self.port = port
        self.client_connections = {}
        self.running = False
        self.lock = asyncio.Lock()

    async def handle_client_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        """
        Handle client connection. Receive data from client and send it to output.
        """
        conn_id = str(uuid4())
        self.client_connections[conn_id] = writer

        # Notify server to create a new connection
        await self._put_output(
            str(
                Message.create(
                    target="client",
                    type=MessageType.NEW_CONNECTION,
                    conn_id=conn_id,
                    data=b"",
                )
            )
        )

        try:
            while self.running:
                data = await reader.read(512)

                if not data:
                    # Connection closed
                    break

                # Send data to output
                await self._put_output(
                    str(
                        Message.create(
                            target="client",
                            type=MessageType.DATA,
                            conn_id=conn_id,
                            data=data,
                        )
                    )
                )
        finally:
            async with self.lock:
                if conn_id in self.client_connections:
                    del self.client_connections[conn_id]
                if writer.transport is not None:
                    # Remove connection from dict and close socket
                    writer.close()
                    await writer.wait_closed()
            # Notify server to close connection
            await self._put_output(
                str(
                    Message.create(
                        target="client",
                        type=MessageType.CLOSE_CONNECTION,
                        conn_id=conn_id,
                        data=b"",
                    )
                )
            )

    async def start_server(self):
        """
        Start server. Accept connections and handle them.
        """
        server = await asyncio.start_server(
            self.handle_client_connection, self.host, self.port
        )

        self.running = True

        async with server:
            await server.serve_forever()

    async def worker(self):
        """
        Worker coroutine. Receive data from input and send it to client.
        """
        try:
            while self.running:
                s = await self._get_input()
                message = Message.from_str(s)
                if not message:
                    continue
                elif message.target != "server":
                    continue
                elif message.type == MessageType.CLOSE_CONNECTION:
                    # Close connection
                    async with self.lock:
                        conn_id = message.conn_id
                        if conn_id in self.client_connections:
                            writer = self.client_connections[conn_id]
                            if writer.transport is not None:
                                writer.close()
                                await writer.wait_closed()
                            del self.client_connections[conn_id]
                elif message.type == MessageType.DATA:
                    # Send data to client
                    conn_id = message.conn_id
                    data = message.data
                    if conn_id in self.client_connections:
                        writer = self.client_connections[conn_id]
                        writer.write(data)
                        await writer.drain()
        finally:
            async with self.lock:
                for writer in self.client_connections.values():
                    if writer.transport is not None:
                        writer.close()
                        await writer.wait_closed()

    async def start(self):
        """
        Start server. Run the server and worker coroutine.
        """
        self.running = True
        await asyncio.gather(self.start_server(), self.worker())

    def stop(self):
        """
        Stop server.
        """
        self.running = False
