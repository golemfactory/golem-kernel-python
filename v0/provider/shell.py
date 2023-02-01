import asyncio
import sys

import click
import zmq
import zmq.asyncio

INPUT_SOCKET_ADDR = "ipc:///tmp/shell_input.sock"
OUTPUT_SOCKET_ADDR = "ipc:///tmp/shell_output.sock"


@click.group()
def cli():
    pass


@cli.command()
def run() -> None:
    async def _run():
        print("Spawning Python subprocess...")
        proc = await asyncio.subprocess.create_subprocess_shell(  # pylint: disable=no-member
            "python3 -i -q",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        input_task = asyncio.create_task(forward_input(proc.stdin))
        output_task = asyncio.create_task(forward_output(proc.stdout))
        try:
            await asyncio.wait({input_task, output_task})
        except asyncio.CancelledError:
            proc.terminate()
            await proc.wait()
            input_task.cancel()
            output_task.cancel()

    loop = asyncio.get_event_loop()
    task = loop.create_task(_run())
    try:
        loop.run_until_complete(task)
    except KeyboardInterrupt:

        task.cancel()
        try:
            loop.run_until_complete(task)
            print("Stopped.")
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass


async def forward_input(writer: asyncio.StreamWriter) -> None:
    print(f"Forwarding input from {INPUT_SOCKET_ADDR}...")
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.constants.REP)
    socket.bind(INPUT_SOCKET_ADDR)
    while True:
        data: bytes = await socket.recv()
        print(f'{data.decode()}', end='', flush=True)
        writer.write(data)
        await writer.drain()
        await socket.send(b'')


async def forward_output(reader: asyncio.StreamReader) -> None:
    print(f"Forwarding output to {OUTPUT_SOCKET_ADDR}...")
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.constants.REP)
    socket.bind(OUTPUT_SOCKET_ADDR)
    while True:
        await socket.recv()
        line: bytes = await reader.read(10000)
        print(line.decode(), end='', flush=True)
        await socket.send(line)


@cli.command()
def write() -> None:
    line = sys.stdin.readline()
    context = zmq.Context()
    socket = context.socket(zmq.constants.REQ)
    socket.connect(INPUT_SOCKET_ADDR)
    socket.send(line.encode())
    socket.recv()


@cli.command()
def read() -> None:
    context = zmq.Context()
    socket = context.socket(zmq.constants.REQ)
    socket.connect(OUTPUT_SOCKET_ADDR)
    socket.send(b'')
    data: bytes = socket.recv()
    if data:
        print(data.decode(), end='', flush=True)


if __name__ == '__main__':
    cli()
