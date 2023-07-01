import logging
import time


def with_logging(cells):
    starting_time = time.time()
    total = len(cells)
    for i, cell in enumerate(cells, 1):
        logging.info(f"Cell {i}/{total}:")
        logging.info("---------")
        logging.info("Input:")
        logging.info(cell["source"])
        yield cell
        logging.info("Output:")
        logging.info("".join(output["text"] for output in cell["outputs"]))
    logging.info("==========")
    finishing_time = time.time()
    logging.info(f"Execution finished in {finishing_time - starting_time:0.1f} seconds")
