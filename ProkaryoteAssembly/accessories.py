import logging
import shutil
from pathlib import Path
from subprocess import Popen, PIPE
from ProkaryoteAssembly.config import DEPENDENCIES, __version__, __author__, __email__


def dependency_check(dependency: str) -> bool:
    """
    Checks if a given program is present in the user's $PATH
    :param dependency: String of program name
    :return: True if program is in $PATH, False if not
    """
    check = shutil.which(dependency)
    if check is not None:
        return True
    else:
        return False


def check_all_dependencies():
    # Dependency check
    logging.info("Conducting dependency check...")
    dependency_dict = dict()
    for dependency in DEPENDENCIES:
        dependency_dict[dependency] = dependency_check(dependency)
    if False in dependency_dict.values():
        logging.error("ERROR: Cannot locate some dependencies in $PATH...")
        for key, value in dependency_dict.items():
            if not value:
                logging.error(f"Dependency missing: {key}")
        quit()
    else:
        for key, value in dependency_dict.items():
            logging.debug(f"Dependency {key}: {value}")
    logging.info("Dependencies OK")


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    logging.info(f"Version: {__version__}")
    logging.info(f"Author: {__author__}")
    logging.info(f"Email: {__email__}")
    quit()


def convert_to_path(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    return Path(value)


def run_subprocess(cmd: str, get_stdout=False):
    if get_stdout:
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        out = out.decode().strip()
        err = err.decode().strip()
        if out != "":
            return out
        elif err != "":
            return err
        else:
            return ""
    else:
        p = Popen(cmd, shell=True)
        p.wait()
