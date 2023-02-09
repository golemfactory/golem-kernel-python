import asyncio
import sys

from golem_core import GolemNode, Payload
from golem_core.mid import (
    Chain, Map, Buffer,
    default_negotiate, default_create_agreement, default_create_activity
)

from golem_kernel.remote_python import RemotePython
from yapapi.payload import vm

PAYLOAD = Payload.from_image_hash(
    "701d57c13726afaf15bf8d602ce0710fc6119d0192507a220cef48d8",
    capabilities=[vm.VM_CAPS_VPN],
)


async def get_activity(golem):
    allocation = await golem.create_allocation(1)
    demand = await golem.create_demand(PAYLOAD, allocations=[allocation])

    chain = Chain(
        demand.initial_proposals(),
        Map(default_negotiate),
        Map(default_create_agreement),
        Map(default_create_activity),
        Buffer(size=1),
    )
    async for activity in chain:
        yield activity

async def async_stdin_reader():
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)
    return reader

async def main():
    golem = GolemNode()

    async with golem:
        async for activity in get_activity(golem):
            print(activity)
            remote_python = RemotePython(activity)
            try:
                await remote_python.start()
            except Exception as e:
                print(f"{activity} failed on startup: {e}")
            else:
                break

        reader = await async_stdin_reader()
        while True:
            print(">>> ", end='', flush=True)
            input_ = (await reader.readline()).decode()
            output = await remote_python.execute(input_)
            if 'stdout' in output:
                print(output['stdout'], flush=True)
            if 'result' in output:
                print("[RESULT] " + output['result'], flush=True)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    task = loop.create_task(main())
    try:
        loop.run_until_complete(task)
    except KeyboardInterrupt:
        task.cancel()
        try:
            loop.run_until_complete(task)
        except asyncio.CancelledError:
            pass
