import sys
import yaml
from pathlib import Path
from loguru import logger as _logger

from metagpt.const import PROJECT_ROOT


def load_config():
    config_path = PROJECT_ROOT / "config/log_config.yaml"
    with config_path.open() as file:
        config = yaml.safe_load(file)
    return config


def get_next_log_filename(log_dir: Path, base_name: str = "log"):
    index = 0
    while True:
        suffix = str(index) if index else ""  # no suffix for the first file
        log_filename = f"{base_name}{suffix}.txt"
        log_filepath = log_dir / log_filename
        if not log_filepath.exists():
            return log_filepath
        index += 1


def define_log_level():
    config = load_config()
    print_level = config.get("print_level", "INFO")
    logfile_level = config.get("logfile_level", "DEBUG")
    logfile_name = config.get("logfile_name", "log")
    print("Print Level:", print_level)
    print("Logfile Level:", logfile_level)

    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)  # ensure the log directory exists

    log_filepath = get_next_log_filename(log_dir, logfile_name)

    _logger.remove()
    new_level = _logger.level("DEVELOP", no=38, color="<red>", icon="🐍")
    _logger.add(sys.stderr, level=print_level)
    _logger.add(log_filepath, level=logfile_level)
    return _logger


logger = define_log_level()
