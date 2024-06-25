from typing import LiteralString, Union

import loguru
import sys
import json

AUTO = -1

def setup(name: Union[LiteralString, bytes] = __name__, level: int = 20):
    if level == AUTO:
        with open("settings.json", "r") as f:
            level = json.load(f).get("log_level", 20)

    logger = loguru.logger
    logger.remove()
    logger.add(sys.stderr, level=level)
    logger.add(f"logs/{name}.log", level=level)

    return logger