import logging
import json
import time
from pathlib import Path

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(
            {
                "ts": time.time().__round__(3),
                "level": record.levelname,
                "msg": record.getMessage(),
                "logger": record.name
            }
        )

def get_logger(
        name="pipeline", log_path="logs/pipeline.log"
        )-> logging.Logger:
    log = logging.getLogger(name)
    log.setLevel(logging.INFO)

    if log.handlers:
        return log # already configured
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(log_path)
    fh.setFormatter(JsonFormatter())
    log.addHandler(fh)
    return log
