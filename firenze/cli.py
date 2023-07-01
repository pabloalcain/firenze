#!/usr/bin/env python3
import asyncio
import json
import logging
import sys

import click

from firenze.notebook import Notebook


# a bit hacky
class PathOrS3(click.Path):
    def convert(self, value, param, ctx):
        if value.startswith("s3://"):
            return value
        return super().convert(value, param, ctx)


@click.command()
@click.argument("notebook-path", type=PathOrS3(exists=True))
@click.option("--output-html-path", type=PathOrS3(), default="output.html")
@click.option("-q", "--quiet", count=True, help="Decrease verbosity.")
@click.argument("parameters", nargs=-1)
def execute_notebook(notebook_path, output_html_path, quiet, parameters):
    parsed_options = parse_options(parameters)
    notebook = Notebook.from_path(notebook_path)
    notebook.clean()
    notebook.set_parameters(**parsed_options)
    done_event = asyncio.Event()

    if quiet:
        logging.basicConfig(level=logging.WARNING, format="%(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    async def execute_and_write():
        async def execute():
            await notebook.async_execute()
            done_event.set()

        async def write_html():
            while not done_event.is_set():
                notebook.write_html(output_html_path)
                await asyncio.sleep(5)

        await asyncio.gather(asyncio.create_task(execute()), asyncio.create_task(write_html()))
        notebook.write_html(output_html_path)

    asyncio.run(execute_and_write())


def parse_options(parameters):
    parsed_options = {}
    for option in parameters:
        name, value = option.split("=", 1)
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            pass
        parsed_options[name] = value
    return parsed_options


if __name__ == "__main__":
    sys.exit(execute_notebook())
