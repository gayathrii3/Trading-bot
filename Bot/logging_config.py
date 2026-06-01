import os
import logging
from pathlib import Path

def setup_logging():
    """
    Configures logging for the trading bot.
    Logs DEBUG and above to Logs/trading_bot.log.
    Logs INFO and above with simple color formatting to the console.
    """
    base_dir = Path(__file__).resolve().parent.parent
    logs_dir = base_dir / 'Logs'
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / 'trading_bot.log'
    
    logger = logging.getLogger('trading_bot')
    logger.setLevel(logging.DEBUG)
    
    # Avoid duplicate handlers if setup_logging is called multiple times
    if logger.handlers:
        return logger
        
    # File handler (detailed debugging information)
    file_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s'
    )
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Console handler (cleaner formatting for CLI output with simple styling)
    class ColorFormatter(logging.Formatter):
        RESET = "\033[0m"
        BOLD = "\033[1m"
        GREEN = "\033[32m"
        YELLOW = "\033[33m"
        RED = "\033[31m"
        CYAN = "\033[36m"
        
        LEVEL_PREFIX = {
            logging.DEBUG: f"{CYAN}[DEBUG] {RESET}",
            logging.INFO: f"{GREEN}[INFO] {RESET}",
            logging.WARNING: f"{YELLOW}[WARNING] {RESET}",
            logging.ERROR: f"{RED}[ERROR] {RESET}",
            logging.CRITICAL: f"{BOLD}{RED}[CRITICAL] {RESET}"
        }
        
        def format(self, record):
            prefix = self.LEVEL_PREFIX.get(record.levelno, "")
            # Apply color to the message body if it is warning or error
            if record.levelno == logging.WARNING:
                msg = f"{self.YELLOW}{record.msg}{self.RESET}"
            elif record.levelno >= logging.ERROR:
                msg = f"{self.RED}{record.msg}{self.RESET}"
            else:
                msg = record.msg
            
            # Format output
            return f"{prefix}{msg}"

    console_formatter = ColorFormatter()
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Keep console clean from too many debug details
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Initialize logger
logger = setup_logging()
