import json
import asyncio
from mitmproxy import http, ctx, options
from mitmproxy.tools.dump import DumpMaster
from asyncio import Queue
from . import IOPlugin

PROXY_HOST = "127.0.0.1"
PROXY_PORT = 8080
URL_PREFIX = "https://example.com"
TERMINALS_CONNECTION = "/terminals/websocket"
START_COMMAND = "python ~/TXTunnel/main.py -s -H 127.0.0.1 -P 7000"
SHORTCUTS = {
    "start": "\u001bOP",
    "stop": "\u0003",
}


class MitmAddon:
    _working_flow: http.HTTPFlow
    input_queue: Queue
    output_queue: Queue
    running: bool

    def __init__(self, input_queue: Queue, output_queue: Queue):
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.running = False

    async def start(self):
        """Start the terminal and handle IO"""
        print("Starting terminal")
        self.running = True
        ctx.master.commands.call(
            "inject.websocket",
            self._working_flow,
            False,
            json.dumps(["stdin", f"\r\n{START_COMMAND}\r\n"]).encode(),
        )
        ctx.master.commands.call(
            "inject.websocket",
            self._working_flow,
            True,
            json.dumps(["stdout", "\r\nServer started."]).encode(),
        )
        while self.running:
            data = await self.input_queue.get()
            ctx.master.commands.call(
                "inject.websocket",
                self._working_flow,
                False,
                json.dumps(["stdin", data]).encode(),
            )

    def stop(self):
        """Stop the terminal"""
        ctx.master.commands.call(
            "inject.websocket",
            self._working_flow,
            False,
            json.dumps(["stdin", "\u0003"]).encode(),
        )
        ctx.master.commands.call(
            "inject.websocket",
            self._working_flow,
            True,
            json.dumps(["stdout", "\r\nServer stoped."]).encode(),
        )
        self.running = False

    async def websocket_message(self, flow: http.HTTPFlow):
        """Handle websocket messages"""
        assert flow.websocket is not None

        if not flow.request.pretty_url.startswith(URL_PREFIX):
            return

        # Ignore non-terminal websocket connections
        if TERMINALS_CONNECTION not in flow.request.pretty_url:
            return

        # Ignore non-text messages
        last_message = flow.websocket.messages[-1]
        if not last_message.is_text:
            return
        print(
            ("Client: " if last_message.from_client else "Server: ") + last_message.text
        )

        if last_message.injected:
            return

        # Parse JSON
        try:
            json_obj = json.loads(last_message.text)
        except json.JSONDecodeError:
            print("Failed to parse JSON")
            return

        # Handle messages
        if not self.running:
            if last_message.from_client:
                if json_obj[0] == "stdin" and json_obj[1] == SHORTCUTS["start"]:
                    # Start terminal
                    asyncio.create_task(self.start())
                    self._working_flow = flow
                    last_message.drop()
        else:
            if self._working_flow != flow:
                return
            if last_message.from_client:
                # Stop terminal
                if json_obj[0] == "stdin" and json_obj[1] == SHORTCUTS["stop"]:
                    self.stop()
            else:
                # Handle stdout
                if json_obj[0] == "stdout":
                    await self.output_queue.put(json_obj[1])
            # Drop message
            last_message.drop()


class MitmIO(IOPlugin):
    input_queue: Queue
    output_queue: Queue
    mitmproxy: DumpMaster

    def __init__(self):
        self.input_queue = Queue()
        self.output_queue = Queue()

    async def put(self, data: str):
        """Put data to the input queue"""
        await self.input_queue.put(data)

    async def get(self) -> str:
        """Get data from the output queue"""
        return await self.output_queue.get()

    async def start(self):
        """Start the proxy"""
        opts = options.Options(listen_host=PROXY_HOST, listen_port=PROXY_PORT)
        self.mitmdump = DumpMaster(opts)
        mitm_addon = MitmAddon(self.input_queue, self.output_queue)
        self.mitmdump.addons.add(mitm_addon)
        await self.mitmdump.run()

    async def stop(self):
        """Stop the proxy"""
        self.mitmdump.shutdown()


PLUGIN = MitmIO
