#!/usr/bin/env python3

""" This module is an entry point of ec2fs app. """


import argparse
import logging
import sys
import typing


__author__ = 'Kamil Janiec <kamil.janiec@nokia.com>'


LOGGER = logging.getLogger(__name__)


def _parse_args(args: typing.List[str]) -> argparse.Namespace:
    """ Return parsed args. """
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true', default=False,
                        help='Turn on debug logging.')
    return parser.parse_args(args)


def _setup_logger(debug: bool = False) -> None:
    """ Configure logging basic configuration. """

    logging_format = ('%(asctime)s - %(threadName)s - '
                      '%(funcName)s - %(levelname)s - '
                      '%(message)s')

    logging_level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(level=logging_level,
                        format=logging_format)


def main() -> None:
    """ Script entrypoint. """
    args = _parse_args(sys.argv[1:])

    _setup_logger(debug=args.debug)

    logging.info('args: %r', args)
    logging.debug('args: %r', args)


if __name__ == '__main__':
    main()
