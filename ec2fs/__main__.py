#!/usr/bin/env python3

""" This module is an entry point of ec2fs app. """


import argparse
import logging
import sys
import typing
import fuse

__author__ = 'Kamil Janiec <kamil.janiec@nokia.com>'


from . import ec2fs, ec2_proxy


LOGGER = logging.getLogger(__name__)


def _parse_args(args: typing.List[str]) -> argparse.Namespace:
    """ Return parsed args. """
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true', default=False,
                        help='Turn on debug logging.')
    parser.add_argument('--mock', action='store_true', default=False,
                        help='Turn on ec2 mock.')
    parser.add_argument('--background', action='store_true', default=False,
                        help='Run as background process.')
    parser.add_argument('--region-name', default='us-east-2')
    parser.add_argument('mountpoint', help='Empty directory where fs will be mounted.')
    return parser.parse_args(args)


def _setup_logger(debug: bool = False) -> None:
    """ Configure logging basic configuration. """

    logging_format = ('%(asctime)s - %(threadName)s - '
                      '%(funcName)s - %(levelname)s - '
                      '%(message)s')

    logging_level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(level=logging_level,
                        format=logging_format)


def _spawn_fuse(region_name, mountpoint, foreground=True):
    fuse.FUSE(
        ec2fs.ec2fs(ec2_proxy.ec2_proxy()),
        mountpoint,
        foreground=foreground,
        allow_other=True,
        attr_timeout=0)


def main() -> None:
    """ Script entrypoint. """
    args = _parse_args(sys.argv[1:])

    _setup_logger(debug=args.debug)

    logging.info('args: %r', args)
    logging.debug('args: %r', args)

    foreground = True if not args.background else False

    if args.mock:
        print('MOCKED')
        import moto
        with moto.mock_ec2():
            _spawn_fuse(args.region_name, args.mountpoint, foreground)
    else:
        _spawn_fuse(args.region_name, args.mountpoint, foreground)


if __name__ == '__main__':
    main()
