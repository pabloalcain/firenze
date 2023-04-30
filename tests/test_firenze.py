import pathlib
from typing import Optional

import pytest
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


def test_loading_one_cell_notebook():
    one_cell_notebook_path = pathlib.Path(__file__).parent / "data/one_cell_notebook.ipynb"
    with open(one_cell_notebook_path) as f:
        jupyter_notebook = nbformat.read(f, as_version=4)
    notebook = Notebook(jupyter_notebook)
    assert notebook.jupyter_notebook == jupyter_notebook


@pytest.mark.slow
def test_execute_notebook():
    one_cell_notebook_path = pathlib.Path(__file__).parent / "data/one_cell_notebook.ipynb"
    with open(one_cell_notebook_path) as f:
        jupyter_notebook = nbformat.read(f, as_version=4)
    notebook = Notebook(jupyter_notebook)
    notebook.execute()
    assert notebook.cells[0]["outputs"][0]["text"] == "Starting Cell 1...\nFinished Cell 1\n"


class DummyClient(NotebookClient):
    def setup_kernel(self):
        class DummyContext:
            def __enter__(self):
                pass

            def __exit__(self, exc_type, exc_value, traceback):
                pass

        return DummyContext()

    def execute_cell(self, cell, index):
        cell["outputs"] = [{"output_type": "stream", "name": "stdout", "text": "Dummy text\n"}]
        current_count = cell.get("execution_count")
        if current_count is None:
            current_count = 0
        cell["execution_count"] = current_count + 1
        cell["metadata"] = {"execution": "Execution data"}


def test_execute_notebook_mocked():
    one_cell_notebook_path = pathlib.Path(__file__).parent / "data/one_cell_notebook.ipynb"
    with open(one_cell_notebook_path) as f:
        jupyter_notebook = nbformat.read(f, as_version=4)
    notebook = Notebook(jupyter_notebook, DummyClient(jupyter_notebook))
    notebook.execute()
    assert notebook.cells[0]["outputs"][0]["text"] == "Dummy text\n"


def test_jupyter_notebook_is_clean():
    one_cell_notebook_path = pathlib.Path(__file__).parent / "data/one_cell_notebook.ipynb"
    with open(one_cell_notebook_path) as f:
        jupyter_notebook = nbformat.read(f, as_version=4)
    notebook = Notebook(jupyter_notebook, DummyClient(jupyter_notebook))
    assert notebook.is_clean()


def test_executed_jupyter_notebook_is_not_clean():
    one_cell_notebook_path = pathlib.Path(__file__).parent / "data/one_cell_notebook.ipynb"
    with open(one_cell_notebook_path) as f:
        jupyter_notebook = nbformat.read(f, as_version=4)
    notebook = Notebook(jupyter_notebook, DummyClient(jupyter_notebook))
    notebook.execute()
    assert not notebook.is_clean()
