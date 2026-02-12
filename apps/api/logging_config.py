import logging
import logging.config


def setup_logging():
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    )

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": log_format,
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "handlers": {
                "console": {
                    "level": "DEBUG",
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "": {  # root logger
                    "handlers": ["console"],
                    "level": "DEBUG",
                    "propagate": True,
                },
                "uvicorn": {
                    "level": "DEBUG",
                    "handlers": ["console"],
                    "propagate": False,
                },
                "uvicorn.error": {
                    "level": "DEBUG",
                    "handlers": ["console"],
                    "propagate": False,
                },
                "uvicorn.access": {
                    "level": "DEBUG",
                    "handlers": ["console"],
                    "propagate": False,
                },
                "httpcore": {
                    "level": "WARNING",
                    "handlers": ["console"],
                    "propagate": False,
                },
                "httpx": {
                    "level": "WARNING",
                    "handlers": ["console"],
                    "propagate": False,
                },
            },
        }
    )

    logging.getLogger("api").debug("Logging initialized successfully with dictConfig")


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
