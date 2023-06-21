import ast
import pathlib
from typing import Any, Optional

import boto3
import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter

from firenze.exceptions import VariableAssignmentError


class Notebook:
    def __init__(
        self,
        notebook: nbformat.notebooknode.NotebookNode,
        client: Optional[NotebookClient] = None,
    ):
        if client is None:
            client = NotebookClient(notebook, timeout=600)
        self.client = client
        self.jupyter_notebook = notebook

    def execute(self, **kwargs):
        for key, value in kwargs.items():
            self.set_first_assignment_of_variable(key, value)
        with self.client.setup_kernel():
            for index, cell in enumerate(self.jupyter_notebook.cells):
                self.client.execute_cell(cell, index)

    @property
    def cells(self):
        return self.jupyter_notebook.cells

    @property
    def code_cells(self):
        return [c for c in self.cells if c["cell_type"] == "code"]

    @property
    def html(self) -> str:
        return HTMLExporter().from_notebook_node(self.jupyter_notebook)[0]

    def is_clean(self) -> bool:
        return all([c["outputs"] == [] for c in self.cells])

    def clean(self):
        for cell in self.jupyter_notebook.cells:
            cell["outputs"] = []
            try:
                del cell["execution_count"]
            except KeyError:
                pass

    @classmethod
    def from_path(cls, notebook_path, client: Optional[NotebookClient] = None):
        if str(notebook_path).startswith("s3://"):
            return cls.from_s3(notebook_path)
        return cls.from_local(client, notebook_path)

    @classmethod
    def from_local(cls, client, notebook_path):
        with open(notebook_path) as f:
            jupyter_notebook = nbformat.read(f, as_version=4)
        return cls(jupyter_notebook, client)

    def get_first_assignment_of_variable(self, variable_name: str):
        for cell in self.code_cells:
            tree = ast.parse(cell["source"])
            for node in ast.walk(tree):
                if not isinstance(node, ast.Assign):
                    continue
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == variable_name:
                        return ast.literal_eval(node.value)

    def set_first_assignment_of_variable(self, variable_name: str, variable_value: Any):
        for cell in self.code_cells:
            try:
                tree = ast.parse(cell["source"])
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.Assign):
                    continue
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == variable_name:
                        node.value = ast.Constant(variable_value)
                        cell["source"] = ast.unparse(tree)
                        return
        raise VariableAssignmentError(
            f"Variable {variable_name} not found. Maybe in a cell with a magic command?"
        )

    @classmethod
    def from_s3(cls, s3_path, s3_client=None):
        if s3_client is None:
            s3_client = boto3.client("s3")
        bucket, key = s3_path.replace("s3://", "").split("/", 1)
        data = s3_client.get_object(Bucket=bucket, Key=key)
        jupyter_notebook = nbformat.reads(data["Body"].read().decode("utf_8"), as_version=4)
        return cls(jupyter_notebook)

    def write_html(self, file_path):
        if file_path.startswith("s3://"):
            self.write_html_to_s3(file_path)
        else:
            self.write_html_to_local(file_path)

    def write_html_to_local(self, file_path):
        pathlib.Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            f.write(self.html)

    def write_html_to_s3(self, s3_path):
        bucket, key = s3_path.replace("s3://", "").split("/", 1)
        s3_client = boto3.client("s3")
        s3_client.put_object(Bucket=bucket, Key=key, Body=self.html)
