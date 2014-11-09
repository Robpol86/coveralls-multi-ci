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

from datetime import datetime
import logging
import os
import sys
import signal

from docopt import docopt
import git

__author__ = '@Robpol86'
__license__ = 'MIT'
__version__ = '1.0.0'
OPTIONS = docopt(__doc__) if __name__ == '__main__' else dict()


class Local(object):
    REPO_TOKEN = os.environ.get('COVERALLS_REPO_TOKEN')
    RUN_AT = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S +0000')
    SERVICE_NAME = 'coveralls_multi_ci'

    def __init__(self):
        self.source_files = source_files()
        self.git = git_stats()


class GenericCI(Local):
    SERVICE_NAME = os.environ.get('CI_NAME')
    SERVICE_NUMBER = os.environ.get('CI_BUILD_NUMBER')
    SERVICE_BUILD_URL = os.environ.get('CI_BUILD_URL')
    SERVICE_BRANCH = os.environ.get('CI_BRANCH')
    SERVICE_PULL_REQUEST = os.environ.get('CI_PULL_REQUEST')


class TravisCI(Local):
    """http://docs.travis-ci.com/user/ci-environment/#Environment-variables"""
    REPO_TOKEN = None
    SERVICE_NAME = 'travis-ci'
    SERVICE_JOB_ID = os.environ.get('TRAVIS_JOB_ID')


class AppVeyor(GenericCI):
    """http://www.appveyor.com/docs/environment-variables"""
    SERVICE_NAME = 'appveyor'


class CircleCI(GenericCI):
    """https://circleci.com/docs/environment-variables"""
    SERVICE_NAME = 'circle-ci'


class Semaphore(GenericCI):
    """https://semaphoreapp.com/docs/available-environment-variables.html"""
    SERVICE_NAME = 'semaphore'


class JenkinsCI(GenericCI):
    """https://wiki.jenkins-ci.org/display/JENKINS/Building+a+software+project"""
    SERVICE_NAME = 'jenkins-ci'


class Codeship(GenericCI):
    """https://codeship.io/documentation/continuous-integration/set-environment-variables/"""
    SERVICE_NAME = 'codeship'


class Bamboo(GenericCI):
    """https://confluence.atlassian.com/display/BAMBOO/Bamboo+variables"""
    SERVICE_NAME = 'bamboo'


def git_stats():
    """Generates a dictionary with metadata about the git repo. Current directory must be inside the repo's root.

    Returns:
    A nested dictionary whose structure matches the JSON data sent to the Coveralls API.
    """
    # Open handle to the repo.
    try:
        this_repo = git.Repo()
    except git.InvalidGitRepositoryError:
        logging.error('InvalidGitRepositoryError raised, probably not in a git repo.')
        return dict()
    this_head = this_repo.heads[0]

    # Get metadata.
    head = dict(
        id=this_head.commit.id,
        author_name=this_head.commit.author.name,
        author_email=this_head.commit.author.email,
        committer_name=this_head.commit.committer.name,
        committer_email=this_head.commit.committer.email,
        message=this_head.commit.message,
    )
    branch = this_repo.active_branch
    remotes = [dict(name=r.name, url=r.url) for r in this_repo.remotes]
    return dict(head=head, branch=branch, remotes=remotes)


def source_files():
    return dict()


def select_ci():
    """Instantiates the appropriate class and returns the instance."""
    if 'CI' in os.environ and 'TRAVIS' in os.environ:
        instance = TravisCI()
    elif 'CI' in os.environ and 'APPVEYOR' in os.environ:
        instance = AppVeyor()
    elif 'CI' in os.environ and 'CIRCLECI' in os.environ:
        instance = CircleCI()
    elif 'CI' in os.environ and 'SEMAPHORE' in os.environ:
        instance = Semaphore()
    elif 'JENKINS_URL' in os.environ:
        instance = JenkinsCI()
    elif 'CI' in os.environ and os.environ.get('CI_NAME') == 'codeship':
        instance = Codeship()
    elif 'bamboo.buildNumber' in os.environ:
        instance = Bamboo()
    else:
        logging.debug('Did not detect an officially supported CI. Trying the generic class.')
        if 'CI_NAME' in os.environ:
            instance = GenericCI()
        else:
            logging.warning('Resorting to Local class. Environment variable "CI_NAME" not defined.')
            instance = Local()
    return instance


def post_to_api():
    pass


def main():
    logging.critical('critical')
    logging.error('error')
    logging.warning('warning')
    logging.info('info')
    logging.debug('debug')


def setup_logging():
    """Called when __name__ == '__main__' below. Sets up logging library.

    If --quiet was used, disables all logging, which is the only way this script writes to the console.

    Otherwise, all CRITICAL, ERROR, and WARNING messages go to stderr, while INFO and DEBUG messages go to stdout. If
    --verbose was used, all levels are enabled. If --verbose was not used, DEBUG messages will be silenced (done at the
    root logger level).
    """
    if OPTIONS.get('--quiet'):
        logging.disable(logging.CRITICAL)
        return
    fmt = '%(asctime)-15s %(levelname)-8s %(funcName)-13s %(message)s' if OPTIONS.get('--verbose') else '%(message)s'

    class InfoFilter(logging.Filter):
        """From http://stackoverflow.com/questions/16061641/python-logging-split-between-stdout-and-stderr"""
        def filter(self, rec):
            return rec.levelno in (logging.DEBUG, logging.INFO)

    handler_stdout = logging.StreamHandler(sys.stdout)
    handler_stdout.setFormatter(logging.Formatter(fmt))
    handler_stdout.setLevel(logging.DEBUG)
    handler_stdout.addFilter(InfoFilter())

    handler_stderr = logging.StreamHandler(sys.stderr)
    handler_stderr.setFormatter(logging.Formatter(fmt))
    handler_stderr.setLevel(logging.WARNING)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if OPTIONS.get('--verbose') else logging.INFO)
    root_logger.addHandler(handler_stdout)
    root_logger.addHandler(handler_stderr)

    logging.debug('coveralls_multi_ci {0}'.format(__version__))

if __name__ == '__main__':
    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))  # Properly handle Control+C
    setup_logging()
    if OPTIONS.get('--version'):
        logging.info('coveralls_multi_ci {0}'.format(__version__))
        sys.exit(0)
    main()
