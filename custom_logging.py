import logging

from loguru import logger

LOG_DAILY_FILE = "logs/{time:YYYY-MM-DD_HH:mm:ss}.log"
LOG_DAILY_DEBUG_FILE = "logs/{time:YYYY-MM-DD_HH:mm:ss}-debug.log"


class InterceptHandler(logging.Handler):
    loglevel_mapping = {
        50: 'CRITICAL',
        40: 'ERROR',
        30: 'WARNING',
        20: 'INFO',
        10: 'DEBUG',
        0: 'NOTSET',
    }

    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except AttributeError:
            level = self.loglevel_mapping[record.levelno]

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logger():
    logger.add(LOG_DAILY_FILE, rotation="00:00", retention="30 days", level="INFO", enqueue=True, backtrace=True)

    # debug级别的日志，生产环境考虑不使用
    logger.add(LOG_DAILY_DEBUG_FILE, rotation="30 seconds", retention="3 days", level="DEBUG", enqueue=True, backtrace=True,
               diagnose=True)

    logging.basicConfig(handlers=[InterceptHandler()], level=0)

    uvicorn_loggers = (
        logging.getLogger(name)
        for name in logging.root.manager.loggerDict
        if name in ["uvicorn", "uvicorn.access", "fastapi"]
    )

    for uvicorn_logger in uvicorn_loggers:
        uvicorn_logger.handlers = [InterceptHandler()]

    return logger.bind(request_id=None, method=None)
