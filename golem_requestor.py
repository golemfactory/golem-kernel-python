#!/usr/bin/env python3
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

from yapapi import Golem
from yapapi.log import enable_default_logger
from yapapi.payload import vm
from yapapi.services import Service

DATE_OUTPUT_PATH = "/golem/work/date.txt"
REFRESH_INTERVAL_SEC = 5


class GolemService(Service):
    @staticmethod
    async def get_payload():
        return await vm.repo(
            image_hash="3522a97c07d6442e5b33cb38abf3a5e33e94d5fb7b6c621a2f9f8fb9",
        )

    async def start(self):
        async for script in super().start():
            yield script

        # every `DATE_POLL_INTERVAL` write output of `date` to `DATE_OUTPUT_PATH`
        script = self._ctx.new_script()
        script.upload_file(str(Path("./repl.py").resolve().absolute()), "/golem/input/repl.py")
        script.run(
            "/bin/bash",
            "-c",
            f"coproc GLM (/usr/local/bin/python3 /golem/input/repl.py) && echo $GLM[@] > ",
        )
        yield script

    async def run(self):
        while True:
            await asyncio.sleep(REFRESH_INTERVAL_SEC)
            script = self._ctx.new_script()
            future_result = script.run(
                "/bin/bash",
                "-c",
                f"cat {DATE_OUTPUT_PATH}",
            )

            yield script

            result = (await future_result).stdout
            print(result.strip() if result else "")


async def main():
    async with Golem(budget=1.0, subnet_tag="devnet-beta") as golem:
        cluster = await golem.run_service(GolemService, num_instances=1)
        start_time = datetime.now()

        while datetime.now() < start_time + timedelta(minutes=1):
            for num, instance in enumerate(cluster.instances):
                print(f"Instance {num} is {instance.state.value} on {instance.provider_name}")
            await asyncio.sleep(REFRESH_INTERVAL_SEC)


if __name__ == "__main__":
    enable_default_logger(log_file="hello.log")

    loop = asyncio.get_event_loop()
    task = loop.create_task(main())
    loop.run_until_complete(task)