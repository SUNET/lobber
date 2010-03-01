# -*- coding: utf-8 -*-

import logging
import logging.handlers

from lobber.settings import LOBBER_LOG_LEVEL

class Logger:
    def __init__(self, subsystem, filename):
        self.subsystem = subsystem
        self.filename = filename
        
        self.logger = logging.getLogger("lobber." + self.subsystem)
        self.logger.setLevel(LOBBER_LOG_LEVEL)

        self.filehandler = logging.FileHandler(self.filename)
        self.filehandler.setLevel(LOBBER_LOG_LEVEL)
        fmter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
        self.filehandler.setFormatter(fmter)
        self.logger.addHandler(self.filehandler)

        self.sysloghandler = logging.handlers.SysLogHandler("/dev/log", facility="local1")
        self.sysloghandler.setLevel(LOBBER_LOG_LEVEL)
        fmter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
        self.sysloghandler.setFormatter(fmter)
        self.logger.addHandler(self.sysloghandler)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)
