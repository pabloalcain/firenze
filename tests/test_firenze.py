import pathlib

import nbclient.exceptions
import pytest
import nbformat
from nbclient import NotebookClient, client

from firenze.notebook import Notebook


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
        cell["outputs"] = [
            nbformat.NotebookNode(
                {"output_type": "stream", "name": "stdout", "text": "Dummy text\n"}
            )
        ]
        current_count = cell.get("execution_count")
        if current_count is None:
            current_count = 0
        cell["execution_count"] = current_count + 1
        cell["metadata"] = nbformat.NotebookNode({"execution": {"something": "Execution data"}})


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


def test_can_clean_executed_jupyter_notebook():
    one_cell_notebook_path = pathlib.Path(__file__).parent / "data/one_cell_notebook.ipynb"
    with open(one_cell_notebook_path) as f:
        jupyter_notebook = nbformat.read(f, as_version=4)
    notebook = Notebook(jupyter_notebook, DummyClient(jupyter_notebook))
    notebook.execute()
    notebook.clean()
    assert notebook.is_clean()


@pytest.mark.slow
def test_notebook_with_error_raises_proper_error():
    notebook_with_error_path = pathlib.Path(__file__).parent / "data/notebook_with_error.ipynb"
    with open(notebook_with_error_path) as f:
        notebook_with_error = nbformat.read(f, as_version=4)
    notebook = Notebook(notebook_with_error)
    with pytest.raises(client.CellExecutionError, match="name 'prinft' is not defined"):
        notebook.execute()


@pytest.mark.slow
def test_clean_notebook_generates_html():
    one_cell_notebook_path = pathlib.Path(__file__).parent / "data/one_cell_notebook.ipynb"
    with open(one_cell_notebook_path) as f:
        jupyter_notebook = nbformat.read(f, as_version=4)
    notebook = Notebook(jupyter_notebook, DummyClient(jupyter_notebook))
    # Don't know how to assert this
    assert "&quot;Starting Cell 1...&quot;" in notebook.html
    assert "Dummy text" not in notebook.html


@pytest.mark.slow
def test_executed_notebook_generates_html():
    one_cell_notebook_path = pathlib.Path(__file__).parent / "data/one_cell_notebook.ipynb"
    with open(one_cell_notebook_path) as f:
        jupyter_notebook = nbformat.read(f, as_version=4)
    notebook = Notebook(jupyter_notebook, DummyClient(jupyter_notebook))
    notebook.execute()
    assert "Dummy text" in notebook.html


@pytest.mark.slow
def test_notebook_that_fails_generates_html():
    notebook_with_error_path = pathlib.Path(__file__).parent / "data/notebook_with_error.ipynb"
    with open(notebook_with_error_path) as f:
        notebook_with_error = nbformat.read(f, as_version=4)
    notebook = Notebook(notebook_with_error)
    with pytest.raises(nbclient.exceptions.CellExecutionError):
        notebook.execute()
    assert "NameError" in notebook.html


def test_load_notebook_from_path():
    one_cell_notebook_path = pathlib.Path(__file__).parent / "data/one_cell_notebook.ipynb"
    notebook = Notebook.from_path(one_cell_notebook_path)
    with open(one_cell_notebook_path) as f:
        jupyter_notebook = nbformat.read(f, as_version=4)
    assert notebook.jupyter_notebook == jupyter_notebook


def test_can_find_variable_in_notebook():
    notebook_with_variables_path = (
        pathlib.Path(__file__).parent / "data/notebook_with_variables.ipynb"
    )
    notebook = Notebook.from_path(notebook_with_variables_path)
    assert notebook.get_first_assignment_of_variable("my_variable") == 4


def test_can_modify_variable_in_notebook():
    notebook_with_variables_path = (
        pathlib.Path(__file__).parent / "data/notebook_with_variables.ipynb"
    )
    notebook = Notebook.from_path(notebook_with_variables_path)
    notebook.set_first_assignment_of_variable("my_variable", 5)
    assert notebook.get_first_assignment_of_variable("my_variable") == 5


def test_cannot_modify_missing_variable_in_notebook():
    notebook_with_variables_path = (
        pathlib.Path(__file__).parent / "data/notebook_with_variables.ipynb"
    )
    notebook = Notebook.from_path(notebook_with_variables_path)
    with pytest.raises(ValueError, match="Variable non_existing_variable not found"):
        notebook.set_first_assignment_of_variable("non_existing_variable", 5)


def test_can_modify_variable_to_a_list():
    notebook_with_variables_path = (
        pathlib.Path(__file__).parent / "data/notebook_with_variables.ipynb"
    )
    notebook = Notebook.from_path(notebook_with_variables_path)
    notebook.set_first_assignment_of_variable("my_variable", [1, 2, 3])
    assert notebook.get_first_assignment_of_variable("my_variable") == [1, 2, 3]
