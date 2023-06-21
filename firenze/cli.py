#!/usr/bin/env python3
import json

import click

from firenze.exceptions import VariableAssignmentError
from firenze.notebook import Notebook

# a bit hacky
class PathOrS3(click.Path):
    def convert(self, value, param, ctx):
        if value.startswith('s3://'):
            return value
        return super().convert(value, param, ctx)

@click.command()
@click.argument("notebook-path", type=PathOrS3(exists=True))
@click.option("--output-html-path", type=click.Path(), default="output.html")
@click.argument("parameters", nargs=-1)
def execute_notebook(notebook_path, output_html_path, parameters):
    parsed_options = parse_options(parameters)
    notebook = Notebook.from_path(notebook_path)
    notebook.clean()
    should_print = True
    try:
        notebook.execute(**parsed_options)
    except Exception as e:
        should_print = not isinstance(e, VariableAssignmentError)
        raise
    finally:
        if should_print:
            notebook.write_html(output_html_path)


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
    execute_notebook()
