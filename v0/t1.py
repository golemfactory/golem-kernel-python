import asyncio

from golem_core import commands, GolemNode, Payload
from golem_core.mid import (
    Chain, Map, Buffer,
    default_negotiate, default_create_agreement, default_create_activity
)

PAYLOAD = Payload.from_image_hash("f27375a678d22d6fb323026a08e8a0d1249a9edbff7236a0fa4c236b")

SCRIPT = '''
for i in {1..10};
do
   date >> x;
   sleep 1;
   echo 'AAA'
done
'''

async def prepare_activity(activity):
    batch = await activity.execute_commands(
        commands.Deploy(),
        commands.Start(),
        commands.Run('nohup python shell.py run > /dev/null &'),
    )
    try:
        await batch.wait(timeout=30)
    finally:
        print(batch.events)

    return activity

async def get_activity(golem):
    allocation = await golem.create_allocation(1)
    demand = await golem.create_demand(PAYLOAD, allocations=[allocation])

    chain = Chain(
        demand.initial_proposals(),
        Map(default_negotiate),
        Map(default_create_agreement),
        Map(default_create_activity),
        Map(prepare_activity),
        Buffer(size=1),
    )
    return await chain.__anext__()

async def main():
    golem = GolemNode()

    async with golem:
        activity = await get_activity(golem)
        print(activity)
        batch = await activity.execute_commands(
            commands.Run('python shell.py read')
        )
        await batch.wait(timeout=10)
        print(batch.events[-1].stdout)


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
