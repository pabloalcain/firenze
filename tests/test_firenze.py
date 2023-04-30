import pathlib

import nbformat


class Notebook:
    def __init__(self, notebook: nbformat.notebooknode.NotebookNode):
        self.jupyter_notebook = notebook


def test_loading_one_cell_notebook():
    one_cell_notebook_path = pathlib.Path(__file__).parent / "data/one_cell_notebook.ipynb"
    with open(one_cell_notebook_path) as f:
        jupyter_notebook = nbformat.read(f, as_version=4)
    notebook = Notebook(jupyter_notebook)
    assert notebook.jupyter_notebook == jupyter_notebook
