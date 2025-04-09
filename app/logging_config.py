import logging
import sys
import json
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.now(timezone.utc) + "Z",
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
            "line_no": record.lineno,
        }
        return json.dumps(log_record)


def configure_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)


if __name__ == "__main__":
    configure_logging()
    logging.info("Logging configured")
