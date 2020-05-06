import sys
from logger import logger
import dlna


def main():
    logger.info("Starting")
    # parameters
    logger.info("Received arguments: %s", sys.argv)
    if len(sys.argv) != 3:
        logger.error("Got %d arguments instead of 3", len(sys.argv))
        exit(1)
    dlna.process(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()
