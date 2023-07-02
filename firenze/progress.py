import asyncio
import itertools
import logging
import time


async def add_elapsed(coro):
    done_event = asyncio.Event()

    async def execute(coro):
        await coro
        done_event.set()

    async def print_elapsed():
        now = asyncio.get_running_loop().time()
        msg = ""
        for char in itertools.cycle("|/-\\"):
            msg = f"...{asyncio.get_running_loop().time() - now:0.1f}s {char}"
            print(msg, end="\r")
            await asyncio.sleep(0.1)
            if done_event.is_set():
                break
        print(" " * len(msg), end="\r")

    await asyncio.gather(execute(coro), asyncio.create_task(print_elapsed()))


def with_logging(cells):
    starting_time = time.time()
    total = len(cells)
    for i, cell in enumerate(cells, 1):
        logging.info(f"Cell {i}/{total}:")
        logging.info("---------")
        logging.info("Input:")
        logging.info(cell["source"])
        yield cell
        logging.info("Output:")
        logging.info("".join(output.get("text", "") for output in cell["outputs"]))
    logging.info("==========")
    finishing_time = time.time()
    logging.info(f"Execution finished in {finishing_time - starting_time:0.1f} seconds")
