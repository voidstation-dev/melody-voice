import json
import logging
from datetime import datetime, timezone


STRUCTURED_FIELDS = (
    "job_id",
    "batch_id",
    "worker_id",
    "attempt",
    "chunk_index",
    "chunk_count",
    "voice_type",
    "text_length",
    "status",
    "duration_ms",
    "error_code",
    "queue_depth",
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in STRUCTURED_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str) -> None:
    root_logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root_logger.handlers = [handler]
    root_logger.setLevel(level.upper())
