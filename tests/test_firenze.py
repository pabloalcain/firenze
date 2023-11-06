import logging
import pathlib
import re
import tempfile

import boto3
import nbclient.exceptions
import nbformat
import pytest
from moto import mock_s3
from nbclient import NotebookClient, client

from firenze.exceptions import VariableAssignmentError
from firenze.notebook import Notebook


class DummyClient(NotebookClient):
    def async_setup_kernel(self):
        class DummyContext:
            async def __aenter__(self):
                pass

            async def __aexit__(self, exc_type, exc_value, traceback):
                pass

        return DummyContext()

    async def async_execute_cell(self, cell, index, **kwargs):
        cell["outputs"] = [
            nbformat.NotebookNode(
                {"output_type": "stream", "name": "stdout", "text": "Dummy text\n"}
            ),
            nbformat.NotebookNode(
                {"output_type": "execute_result", "metadata": {}, "data": {}, "execution_count": 1}
            ),
        ]


class DummyClientWithNoTextOutputs(DummyClient):
    async def async_execute_cell(self, cell, index, **kwargs):
        cell["outputs"] = [
            nbformat.NotebookNode(
                {"output_type": "execute_result", "metadata": {}, "data": {}, "execution_count": 1}
            ),
        ]


@pytest.fixture
def one_cell_notebook_path():
    return pathlib.Path(__file__).parent / "data/one_cell_notebook.ipynb"


@pytest.fixture
def notebook_with_error_path():
    return pathlib.Path(__file__).parent / "data/notebook_with_error.ipynb"


@pytest.fixture
def notebook_with_variables_path():
    return pathlib.Path(__file__).parent / "data/notebook_with_variables.ipynb"


def test_loading_one_cell_notebook(one_cell_notebook_path):
    with open(one_cell_notebook_path) as f:
        jupyter_notebook = nbformat.read(f, as_version=4)
    notebook = Notebook(jupyter_notebook)
    assert notebook.jupyter_notebook == jupyter_notebook


@pytest.mark.slow
def test_execute_notebook(one_cell_notebook_path):
    with open(one_cell_notebook_path) as f:
        jupyter_notebook = nbformat.read(f, as_version=4)
    notebook = Notebook(jupyter_notebook)
    notebook.execute()
    assert notebook.cells[0]["outputs"][0]["text"] == "Starting Cell 1...\nFinished Cell 1\n"


def test_execute_notebook_mocked(one_cell_notebook_path):
    with open(one_cell_notebook_path) as f:
        jupyter_notebook = nbformat.read(f, as_version=4)
    notebook = Notebook(jupyter_notebook, DummyClient(jupyter_notebook))
    notebook.execute()
    assert notebook.cells[0]["outputs"][0]["text"] == "Dummy text\n"


def test_jupyter_notebook_is_clean(one_cell_notebook_path):
    with open(one_cell_notebook_path) as f:
        jupyter_notebook = nbformat.read(f, as_version=4)
    notebook = Notebook(jupyter_notebook, DummyClient(jupyter_notebook))
    assert notebook.is_clean()


def test_executed_jupyter_notebook_is_not_clean(one_cell_notebook_path):
    with open(one_cell_notebook_path) as f:
        jupyter_notebook = nbformat.read(f, as_version=4)
    notebook = Notebook(jupyter_notebook, DummyClient(jupyter_notebook))
    notebook.execute()
    assert not notebook.is_clean()


def test_can_clean_executed_jupyter_notebook(one_cell_notebook_path):
    with open(one_cell_notebook_path) as f:
        jupyter_notebook = nbformat.read(f, as_version=4)
    notebook = Notebook(jupyter_notebook, DummyClient(jupyter_notebook))
    notebook.execute()
    notebook.clean()
    assert notebook.is_clean()


@pytest.mark.slow
def test_notebook_with_error_raises_proper_error(notebook_with_error_path):
    with open(notebook_with_error_path) as f:
        notebook_with_error = nbformat.read(f, as_version=4)
    notebook = Notebook(notebook_with_error)
    with pytest.raises(client.CellExecutionError, match="name 'prinft' is not defined"):
        notebook.execute()


@pytest.mark.slow
def test_clean_notebook_generates_html(one_cell_notebook_path):
    with open(one_cell_notebook_path) as f:
        jupyter_notebook = nbformat.read(f, as_version=4)
    notebook = Notebook(jupyter_notebook, DummyClient(jupyter_notebook))
    # Don't know how to assert this
    assert "&quot;Starting Cell 1...&quot;" in notebook.html
    assert "Dummy text" not in notebook.html


@pytest.mark.slow
def test_executed_notebook_generates_html(one_cell_notebook_path):
    with open(one_cell_notebook_path) as f:
        jupyter_notebook = nbformat.read(f, as_version=4)
    notebook = Notebook(jupyter_notebook, DummyClient(jupyter_notebook))
    notebook.execute()
    assert "Dummy text" in notebook.html


@pytest.mark.slow
def test_notebook_that_fails_generates_html(notebook_with_error_path):
    with open(notebook_with_error_path) as f:
        notebook_with_error = nbformat.read(f, as_version=4)
    notebook = Notebook(notebook_with_error)
    with pytest.raises(nbclient.exceptions.CellExecutionError):
        notebook.execute()
    assert "NameError" in notebook.html


def test_load_notebook_from_path(one_cell_notebook_path):
    notebook = Notebook.from_path(one_cell_notebook_path)
    with open(one_cell_notebook_path) as f:
        jupyter_notebook = nbformat.read(f, as_version=4)
    assert notebook.jupyter_notebook == jupyter_notebook


def test_can_find_variable_in_notebook(notebook_with_variables_path):
    notebook = Notebook.from_path(notebook_with_variables_path)
    assert notebook.get_first_assignment_of_variable("my_variable") == 4


def test_can_modify_variable_in_notebook(notebook_with_variables_path):
    notebook = Notebook.from_path(notebook_with_variables_path)
    notebook.set_first_assignment_of_variable("my_variable", 5)
    assert notebook.get_first_assignment_of_variable("my_variable") == 5


def test_cannot_modify_missing_variable_in_notebook(notebook_with_variables_path):
    notebook = Notebook.from_path(notebook_with_variables_path)
    with pytest.raises(
        VariableAssignmentError,
        match="Variable non_existing_variable not found. Maybe in a cell with a magic command?",
    ):
        notebook.set_first_assignment_of_variable("non_existing_variable", 5)


def test_can_modify_variable_to_a_list(notebook_with_variables_path):
    notebook = Notebook.from_path(notebook_with_variables_path)
    notebook.set_first_assignment_of_variable("my_variable", [1, 2, 3])
    assert notebook.get_first_assignment_of_variable("my_variable") == [1, 2, 3]


@pytest.mark.slow
def test_execute_notebook_with_parameters(notebook_with_variables_path):
    notebook = Notebook.from_path(notebook_with_variables_path)
    notebook.set_parameters(my_variable=5)
    notebook.execute()
    assert notebook.cells[0]["outputs"][0]["text"] == "My variable is 5\n"


def test_dummy_execute_notebook_with_parameters(notebook_with_variables_path):
    with open(notebook_with_variables_path) as f:
        jupyter_notebook = nbformat.read(f, as_version=4)
    notebook = Notebook(jupyter_notebook, DummyClient(jupyter_notebook))
    notebook.set_parameters(my_variable=5)
    notebook.execute()
    assert notebook.get_first_assignment_of_variable("my_variable") == 5


def test_dummy_execute_notebook_with_magic_and_parameters():
    notebook_with_variables_path = (
        pathlib.Path(__file__).parent / "data/notebook_with_variables_and_magic.ipynb"
    )
    with open(notebook_with_variables_path) as f:
        jupyter_notebook = nbformat.read(f, as_version=4)
    notebook = Notebook(jupyter_notebook, DummyClient(jupyter_notebook))
    notebook.set_parameters(my_variable=5)
    notebook.execute()
    assert (
        notebook.code_cells[2]["source"]
        == "my_variable = 5\nprint(f'My variable is {my_variable}')"
    )


@pytest.fixture
def mock_bucket(one_cell_notebook_path):
    moto_fake = mock_s3()
    try:
        moto_fake.start()
        conn = boto3.client("s3")
        conn.create_bucket(Bucket="notebooks")
        conn.upload_file(
            Filename=one_cell_notebook_path,
            Bucket="notebooks",
            Key="one_cell_notebook.ipynb",
        )
        yield
    finally:
        moto_fake.stop()


def test_can_load_notebook_from_s3(mock_bucket, one_cell_notebook_path):
    notebook = Notebook.from_s3("s3://notebooks/one_cell_notebook.ipynb")
    with open(one_cell_notebook_path) as f:
        jupyter_notebook = nbformat.read(f, as_version=4)
    assert notebook.jupyter_notebook == jupyter_notebook


@pytest.mark.slow
def test_can_write_notebook_html_to_local_file(one_cell_notebook_path):
    with open(one_cell_notebook_path) as f:
        jupyter_notebook = nbformat.read(f, as_version=4)
    notebook = Notebook(jupyter_notebook, DummyClient(jupyter_notebook))
    notebook.execute()

    with tempfile.NamedTemporaryFile(delete=True) as tmp:
        notebook.write_html(tmp.name)
        assert "Dummy text" in tmp.read().decode("utf-8")


@pytest.mark.slow
def test_can_write_notebook_ipynb_to_local_file(one_cell_notebook_path):
    with open(one_cell_notebook_path) as f:
        jupyter_notebook = nbformat.read(f, as_version=4)
    notebook = Notebook(jupyter_notebook, DummyClient(jupyter_notebook))
    notebook.execute()

    with tempfile.NamedTemporaryFile(delete=True) as tmp:
        notebook.save_notebook(tmp.name)
        new_notebook = Notebook.from_path(tmp.name)
        assert new_notebook.jupyter_notebook == notebook.jupyter_notebook


@pytest.mark.slow
def test_can_write_notebook_html_to_s3_path(mock_bucket, one_cell_notebook_path):
    with open(one_cell_notebook_path) as f:
        jupyter_notebook = nbformat.read(f, as_version=4)
    notebook = Notebook(jupyter_notebook, DummyClient(jupyter_notebook))
    notebook.execute()

    notebook.write_html("s3://notebooks/even_further/one_cell_notebook.html")
    s3 = boto3.resource("s3")
    obj = s3.Object("notebooks", "even_further/one_cell_notebook.html")
    assert "Dummy text" in obj.get()["Body"].read().decode("utf-8")


def test_can_load_notebook_from_s3_with_from_path_constructor(mock_bucket, one_cell_notebook_path):
    notebook_with_variables_path = one_cell_notebook_path
    notebook = Notebook.from_path("s3://notebooks/one_cell_notebook.ipynb")
    with open(notebook_with_variables_path) as f:
        jupyter_notebook = nbformat.read(f, as_version=4)
    assert notebook.jupyter_notebook == jupyter_notebook


@pytest.mark.slow
def test_notebook_execution_logs_input_and_output(caplog, one_cell_notebook_path):
    with open(one_cell_notebook_path) as f:
        jupyter_notebook = nbformat.read(f, as_version=4)
    notebook = Notebook(jupyter_notebook, DummyClient(jupyter_notebook))

    with caplog.at_level(logging.INFO):
        notebook.execute()
    log_records = [i.msg for i in caplog.records]
    expected_patterns = [
        "Cell 1/1:",
        "---------",
        "Input:",
        re.escape('print("Starting Cell 1...")\nprint("Finished Cell 1")\n'),
        "Output:",
        "Dummy text\n",
        "==========",
        re.compile(r"^Execution finished in [0-9\.]+ seconds$"),
    ]
    assert len(expected_patterns) == len(log_records)
    for expected_pattern, record in zip(expected_patterns, log_records):
        assert re.match(expected_pattern, record)


@pytest.mark.slow
def test_execute_notebook_without_outputs(caplog, one_cell_notebook_path):
    with open(one_cell_notebook_path) as f:
        jupyter_notebook = nbformat.read(f, as_version=4)
    notebook = Notebook(jupyter_notebook, DummyClientWithNoTextOutputs(jupyter_notebook))

    with caplog.at_level(logging.INFO):
        notebook.execute()
    log_records = [i.msg for i in caplog.records]
    expected_patterns = [
        "Cell 1/1:",
        "---------",
        "Input:",
        re.escape('print("Starting Cell 1...")\nprint("Finished Cell 1")\n'),
        "Output:",
        "",
        "==========",
        re.compile(r"^Execution finished in [0-9\.]+ seconds$"),
    ]
    assert len(expected_patterns) == len(log_records)
    for expected_pattern, record in zip(expected_patterns, log_records):
        assert re.match(expected_pattern, record)
