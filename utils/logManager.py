import logging
import os
from datetime import datetime

class LogManager:
    loggers = {}
    # logging.getLogger('werkzeug').setLevel(logging.ERROR)
    
    def __init__(self, title):
        self.title = title or "系統訊息"
        
        # 檢查是否已經存在此標題的日誌
        if title in LogManager.loggers:
            self.logger = LogManager.loggers[title]
            return
            
        self.current_date = datetime.now().strftime('%Y%m%d')
        self.logger = logging.getLogger(title)
        self.logger.setLevel(logging.INFO)
        self.file_handler = None
        
        if not self.logger.handlers:
            self._update_file_handler()
            
        LogManager.loggers[title] = self.logger

    def _update_file_handler(self):
        """更新 FileHandler 至新的日期檔案"""
        # 確保 logs 目錄存在
        log_dir = './logs'
        os.makedirs(log_dir, exist_ok=True)
        
        log_filename = os.path.join(log_dir, f"{self.current_date}.log")

        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        self.file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        formatter = logging.Formatter(f'%(asctime)s - %(levelname)s - {self.title} - %(message)s')
        self.file_handler.setFormatter(formatter)
        self.logger.addHandler(self.file_handler)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        self.logger.addHandler(stream_handler)

    def check_date_and_update(self):
        """檢查是否需要更新日期檔案"""
        new_date = datetime.now().strftime('%Y%m%d')
        if hasattr(self, 'current_date') and new_date != self.current_date:
            self.current_date = new_date
            self._update_file_handler()