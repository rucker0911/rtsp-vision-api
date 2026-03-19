import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

_TZ = ZoneInfo("Asia/Taipei")


class LogManager:
    loggers = {}

    def __init__(self, title: str):
        self.title = title or "系統訊息"

        if title in LogManager.loggers:
            self.logger = LogManager.loggers[title]
            return

        self.current_date = datetime.now(_TZ).strftime("%Y%m%d")
        self.logger = logging.getLogger(title)
        self.logger.setLevel(logging.INFO)
        self.file_handler = None

        if not self.logger.handlers:
            self._update_file_handler()

        LogManager.loggers[title] = self.logger

    def _update_file_handler(self):
        log_dir = "./logs"
        os.makedirs(log_dir, exist_ok=True)

        log_filename = os.path.join(log_dir, f"{self.current_date}.log")

        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        formatter = logging.Formatter(
            f"%(asctime)s - %(levelname)s - {self.title} - %(message)s"
        )
        formatter.converter = lambda *args: datetime.now(_TZ).timetuple()

        file_handler = logging.FileHandler(log_filename, encoding="utf-8")
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        self.logger.addHandler(stream_handler)

    def _check_date(self):
        new_date = datetime.now(_TZ).strftime("%Y%m%d")
        if hasattr(self, "current_date") and new_date != self.current_date:
            self.current_date = new_date
            self._update_file_handler()

    def info(self, message: str):
        self._check_date()
        self.logger.info(message)

    def warning(self, message: str):
        self._check_date()
        self.logger.warning(message)

    def error(self, message: str):
        self._check_date()
        self.logger.error(message)

    def debug(self, message: str):
        self._check_date()
        self.logger.debug(message)