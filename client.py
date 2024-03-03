import asyncio
import base64
from typing import Callable
from message import Message, MessageType


class Client:
    host: str
    port: int
    _get_input: Callable[[], str]
    _put_output: Callable[[str], None]
    client_connections: dict[str, asyncio.StreamWriter]
    running: bool
    lock: asyncio.Lock

    def __init__(
        self,
        input_callback: Callable[[], str],
        output_callback: Callable[[str], None],
        host: str = "localhost",
        port: int = 8080,
    ):
        self._get_input = input_callback
        self._put_output = output_callback
        self.host = host
        self.port = port
        self.client_connections = {}
        self.running = False
        self.lock = asyncio.Lock()

    async def handle_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, conn_id: str
    ):
        """
        Handle client connection. Receive data from client and send it to output.
        """
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
                            target="server",
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
                    try:
                        await writer.wait_closed()
                    except ConnectionAbortedError:
                        pass
            # Send close message to output
            await self._put_output(
                str(
                    Message.create(
                        target="server",
                        type=MessageType.CLOSE_CONNECTION,
                        conn_id=conn_id,
                        data=b"",
                    )
                )
            )

    async def start(self):
        """
        Start client. Receive data from input and send it to server.
        """
        self.running = True
        try:
            while self.running:
                s = await self._get_input()
                message = Message.from_str(s)
                if not message:
                    continue
                elif message.target != "client":
                    continue
                elif message.type == MessageType.NEW_CONNECTION:
                    # New connection
                    conn_id = message.conn_id
                    if conn_id not in self.client_connections:
                        reader, writer = await asyncio.open_connection(
                            self.host, self.port
                        )
                        self.client_connections[conn_id] = writer
                        asyncio.create_task(
                            self.handle_connection(reader, writer, conn_id)
                        )
                elif message.type == MessageType.CLOSE_CONNECTION:
                    # Close connection
                    async with self.lock:
                        conn_id = message.conn_id
                        if conn_id in self.client_connections:
                            writer = self.client_connections[conn_id]
                            if writer.transport is not None:
                                writer.close()
                                try:
                                    await writer.wait_closed()
                                except ConnectionAbortedError:
                                    pass
                            del self.client_connections[conn_id]
                elif message.type == MessageType.DATA:
                    # Send data to server
                    conn_id = message.conn_id
                    data = message.data
                    if conn_id in self.client_connections:
                        writer = self.client_connections[conn_id]
                        writer.write(data)
                        await writer.drain()
        finally:
            # Close all connections
            async with self.lock:
                for conn_id, writer in self.client_connections.items():
                    if writer.transport is not None:
                        writer.close()
                        try:
                            await writer.wait_closed()
                        except ConnectionAbortedError:
                            pass

    def stop(self):
        """
        Stop client.
        """
        self.running = False
