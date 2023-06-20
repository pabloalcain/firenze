# Firenze

Firenze is a lean jupyter notebook executor, that generates the notebook output in a single HTML
file. You can also parameterize the notebooks without any modification to the notebook itself.
It supports local files and `s3` paths, both for the notebook and for the output.

## As a Library
You can use `firenze` as a library in your own project. Install it through `pip`

```bash
pip install firenze
```

Suppose you have a very simple notebook that runs a "Hello, World!"

![A notebook in jupyter](docs/img/hello_world_in_jupyter.png)

You can execute it right away with `firenze` through
```bash
firenze docs/notebooks/hello_world.ipynb
```
and the output html will be, as expected:

![Hello, World! output](docs/img/hello_world_output.png)

You can also send parameters and `firenze` will automatically modify the variable:

```bash
firenze docs/notebooks/hello_world.ipynb name=Firenze
```

![Hello, Firenze! output](docs/img/hello_world_with_parameters.png)

## As a Docker Image
This is still in the making, but one idea is to call `firenze` as a docker image with a notebook
and a `requirements.txt`, so the notebook execution can be easily deployed to remote servers.
