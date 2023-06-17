from typing import Optional, Any

import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter

import ast


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
            del cell["execution_count"]

    @classmethod
    def from_path(cls, notebook_path, client: Optional[NotebookClient] = None):
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
            tree = ast.parse(cell["source"])
            for node in ast.walk(tree):
                if not isinstance(node, ast.Assign):
                    continue
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == variable_name:
                        node.value = ast.Constant(variable_value)
                        cell["source"] = ast.unparse(tree)
                        return
        raise ValueError(f"Variable {variable_name} not found")
