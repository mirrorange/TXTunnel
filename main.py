from server import Server
from client import Client
from plugins import IOPlugin
from importlib import import_module
import asyncio


def main(mode: str, host: str, port: int, io_plugin: str):
    """Main function"""
    plugin: IOPlugin = getattr(import_module("plugins." + io_plugin), "PLUGIN")()
    if mode == "server":
        tunnel = Server(
            input_callback=plugin.get,
            output_callback=plugin.put,
            host=host,
            port=port,
        )
    else:
        tunnel = Client(
            input_callback=plugin.get,
            output_callback=plugin.put,
            host=host,
            port=port,
        )
    asyncio.get_event_loop().run_until_complete(
        asyncio.gather(tunnel.start(), plugin.start())
    )
    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Simple tcp tunnel via text")
    parser.add_argument(
        "-s",
        "--server",
        action="store_true",
        help="Run as server",
    )
    parser.add_argument(
        "-c",
        "--client",
        action="store_true",
        help="Run as client",
    )
    parser.add_argument(
        "-H",
        "--host",
        type=str,
        default="localhost",
        help="host to listen on (server) or connect to (client)",
    )
    parser.add_argument(
        "-P",
        "--port",
        type=int,
        default=8080,
        help="port to listen on (server) or connect to (client)",
    )
    parser.add_argument(
        "-p",
        "--plugin",
        type=str,
        default="stdio",
        help="input/output plugin",
    )
    args = parser.parse_args()
    if args.server and args.client:
        raise ValueError("Cannot run as both server and client")
    if not args.server and not args.client:
        raise ValueError("Must run as either server or client")
    main(
        mode="server" if args.server else "client",
        host=args.host,
        port=args.port,
        io_plugin=args.plugin,
    )
