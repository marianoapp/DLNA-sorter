import os.path
import logging
import utils

logger = None


def configure_logger():
    global logger
    log_path = os.path.join(utils.get_base_folder(), "dlna.log")
    logging.basicConfig(filename=log_path, format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO)
    logger = logging.getLogger(__name__)


configure_logger()
