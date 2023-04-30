from typing import Optional

import nbformat
from nbclient import NotebookClient


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

    def execute(self):
        with self.client.setup_kernel():
            for index, cell in enumerate(self.jupyter_notebook.cells):
                self.client.execute_cell(cell, index)

    @property
    def cells(self):
        return self.jupyter_notebook.cells

    def is_clean(self) -> bool:
        return all([c["outputs"] == [] for c in self.cells])

    def clean(self):
        for cell in self.jupyter_notebook.cells:
            cell["outputs"] = []
            del cell["execution_count"]
