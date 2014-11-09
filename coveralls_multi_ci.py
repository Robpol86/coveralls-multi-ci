#!/usr/bin/env python
"""Submits coverage results to Coveralls.io through their API.

TODO

Usage:
    coveralls_multi_ci submit [-q|-v]
    coveralls_multi_ci -h | --help
    coveralls_multi_ci -V | --version

Options:
    -h --help       Show this screen.
    -q --quiet      Print nothing to console.
    -v --verbose    Print debug information to console.
    -V --version    Show version.
"""

import logging
import sys
import signal

from docopt import docopt

__author__ = '@Robpol86'
__license__ = 'MIT'
__version__ = '1.0.0'
OPTIONS = docopt(__doc__) if __name__ == '__main__' else dict()


def main():
    logging.critical('critical')
    logging.error('error')
    logging.warning('warning')
    logging.info('info')
    logging.debug('debug')


if __name__ == '__main__':
    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))  # Properly handle Control+C
    if OPTIONS.get('--quiet'):
        logging.disable(logging.CRITICAL)
    else:
        logging.basicConfig(level=logging.DEBUG if OPTIONS.get('--verbose') else logging.INFO, stream=sys.stdout,
                            format='%(message)s')
    if OPTIONS.get('--version'):
        logging.info('coveralls_multi_ci {0}'.format(__version__))
        sys.exit(0)
    main()
