import shlex

from golem_core import commands


class RemotePython:
    def __init__(self, activity, *, start_timeout=300, batch_timeout=300):
        self.activity = activity
        self.start_timeout = start_timeout
        self.batch_timeout = batch_timeout

    async def start(self):
        batch = await self.activity.execute_commands(
            commands.Deploy(),
            commands.Start(),
            commands.Run('nohup python python_server.py > /dev/null 2>&1 &'),
        )
        await batch.wait(timeout=100)

        #   IMPORTANT: wait until the service starts
        #   (FIXME: better implementation)
        import asyncio
        await asyncio.sleep(10)

        batch = await self.activity.execute_commands(
            commands.Run('python example_client.py'),
        )
        await batch.wait(timeout=10)
        print(batch.events)

        return batch.events[-1].stdout.strip()

    async def execute(self, input_):
        input_ = shlex.quote(input_)
        batch = await self.activity.execute_commands(
            commands.Run(f'echo {input_} | python shell.py write'),
            commands.Run('python shell.py read'),
        )
        await batch.wait(timeout=self.batch_timeout)
        return batch.events[-1].stdout.strip()
