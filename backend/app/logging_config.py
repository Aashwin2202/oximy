import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        stream=sys.stdout,
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
        force=True,
    )
    # Quiet noisy libraries.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
