# Firenze

Firenze is a lean jupyter notebook executor, that generates the notebook output in a single HTML
file.

[![CI](https://github.com/pabloalcain/firenze/actions/workflows/ci.yaml/badge.svg)](https://github.com/pabloalcain/firenze/actions/workflows/ci.yaml)
[![Coverage](https://codecov.io/gh/pabloalcain/firenze/branch/main/graph/badge.svg?token=VJGXI1MVOF)](https://codecov.io/gh/pabloalcain/firenze)
[![License](https://img.shields.io/badge/license-MIT-blue)](https://github.com/pabloalcain/firenze/blob/main/LICENSE.md)
[![Python](https://img.shields.io/pypi/pyversions/firenze)](https://pypi.org/project/firenze/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-black.svg)](https://github.com/ambv/black)
[![PyPI](https://img.shields.io/pypi/v/firenze)](https://pypi.org/project/firenze/)
[![Downloads](https://img.shields.io/pypi/dm/firenze)](https://pypi.org/project/firenze/)

You can also parameterize the notebooks without any modification to the notebook itself.
It supports local files and `s3` paths, both for the notebook and for the output.

## As a Library
You can use `firenze` as a library in your own project. Install it through `pip`

```bash
pip install firenze
```

Suppose you have a very simple notebook that runs a "Hello, World!"

![A notebook in jupyter](https://github.com/pabloalcain/firenze/blob/main/docs/img/hello_world_in_jupyter.png?raw=true)

You can execute it right away with `firenze` through
```bash
firenze docs/notebooks/hello_world.ipynb
```
and the output html will be, as expected:

![Hello, World! output](https://github.com/pabloalcain/firenze/blob/main/docs/img/hello_world_output.png?raw=true)

You can also send parameters and `firenze` will automatically modify the variable:

```bash
firenze docs/notebooks/hello_world.ipynb name=Firenze
```

![Hello, Firenze! output](https://github.com/pabloalcain/firenze/blob/main/docs/img/hello_world_with_parameters.png?raw=true)

## As a Docker Image
This is still in the making, but one idea is to call `firenze` as a docker image with a notebook
and a `requirements.txt`, so the notebook execution can be easily deployed to remote servers.
