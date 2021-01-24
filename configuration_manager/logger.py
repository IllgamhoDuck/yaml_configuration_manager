
import logging

class InfoLogger:
    """Automatic handler, format, level setting for INFO logger

    ### logging.getLogger(name) ###
    Get the logger from the global configuration logging
    If the logger doesn't exist it will be intialized
    """
    def __init__(self, name):
        # Get the logger by the name
        self.logger = logging.getLogger(name)

        # check does previous handler exist
        # to prevent multiple handler in one logger
        if self.logger.handlers:
            return

        # Set level for logger
        self.logger.setLevel(logging.INFO)

        # set handler - stream (console) / file (file)
        stream_handler = logging.StreamHandler()

        # set format - message output format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        stream_handler.setFormatter(formatter)

        self.logger.addHandler(stream_handler)

        # block propagate
        self.logger.propagate = 0

    def info(self, message):
        self.logger.info(message)
