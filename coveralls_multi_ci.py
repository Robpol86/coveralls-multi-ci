#!/usr/bin/env python
"""Submits coverage results to Coveralls.io through their API.

Usually you just need to run:
    coveralls_multi_ci submit

The following are CIs that are natively supported:
    Travis CI (including Pro)
    AppVeyor (COVERALLS_REPO_TOKEN required)
    CircleCI
    Semaphore
    Jenkins
    Codeship (COVERALLS_REPO_TOKEN required)
    Atlassian Bamboo (COVERALLS_REPO_TOKEN required)

If you're using one of the CIs listed above, you don't need to define any
environment variables unless specified, coveralls_multi_ci should work out of
the box. Otherwise you'll need to define these environment variables.
COVERALLS_REPO_TOKEN is the only mandatory variable, the others help though.
    COVERALLS_REPO_TOKEN -- secret repo token displayed on the blue side-bar on
        your project's Coveralls.io page.
    CI_NAME -- Continuous integration provider's name.
    CI_BUILD_NUMBER -- build number, usually 0 is the first time that CI
        builds/tests your project.
    CI_BUILD_URL -- URL to the CI provider's build page.
    CI_BRANCH -- git branch name being built (master, feature, tag's name).
    CI_PULL_REQUEST -- pull request number or "false".

Usage:
    coveralls_multi_ci submit [options]
    coveralls_multi_ci -h | --help
    coveralls_multi_ci -V | --version

Options:
    -c --coverage=FILE  Path to the coverage file generated by Coverage.
                        [default: .coverage]
    -g --git=DIR        Path to the root git repo directory.
                        [default: cwd]
    -h --help           Show this screen.
    --no-delete         Don't delete the temporary payload file after POSTing.
    -o --output=FILE    Temporary payload file to write/read. Dumps all source
                        code into this file and reads it during POST to API.
                        [default: coveralls_multi_ci_payload.txt]
    -q --quiet          Print nothing to console.
    -s --source=FILE    Path to source code root directory.
                        [default: cwd]
    -v --verbose        Print debug information to console.
    -V --version        Show version.
"""

from base64 import b64decode, b64encode
from datetime import datetime
import json
import logging
import os
import re
import signal
import sys

from coverage import coverage
from docopt import docopt
import requests

try:
    import subprocess32
except ImportError:
    import subprocess as subprocess32

__author__ = '@Robpol86'
__license__ = 'MIT'
__version__ = '1.0.0'
_RE_SPLIT = re.compile(r'(PLACEHOLDER_(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?_)')
API_URL = 'https://coveralls.io/api/v1/jobs'
CWD = os.getcwd()
OPTIONS = docopt(__doc__) if __name__ == '__main__' else dict()
RUN_AT = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S +0000')


class Base(object):
    """Base class for all other CI classes."""
    REPO_TOKEN = os.environ.get('COVERALLS_REPO_TOKEN')
    SERVICE_BRANCH = None
    SERVICE_BUILD_URL = None
    SERVICE_JOB_ID = None
    SERVICE_NAME = 'coveralls_multi_ci'
    SERVICE_NUMBER = None
    SERVICE_PULL_REQUEST = None

    @classmethod
    def payload(cls, coverage_result, git_stats_result=None):
        """Puts together environment variable data and coverage/git data into a final dict to be submitted to the API.

        Positional arguments:
        coverage_result -- return value of coverage_report(), which is a dict with each file's source code (the entire
            source code), file name, and coverage information. Will be passed to the API unchanged.

        Keyword arguments:
        git_stats_result -- return value of git_stats(), may be an empty dict or None since API says it's optional. Is
            a dict with some data about the git repo. Will be passed to the API unchanged.

        Returns:
        Final dict meant to be sent as a JSON to the API.
        """
        result = dict(source_files=coverage_result, run_at=RUN_AT)

        # Insert optional values.
        optional = (
            ('git', git_stats_result),
            ('repo_token', cls.REPO_TOKEN),
            ('service_branch', cls.SERVICE_BRANCH),
            ('service_build_url', cls.SERVICE_BUILD_URL),
            ('service_job_id', cls.SERVICE_JOB_ID),
            ('service_name', cls.SERVICE_NAME),
            ('service_number', cls.SERVICE_NUMBER),
            ('service_pull_request', cls.SERVICE_PULL_REQUEST),
        )
        result.update((k, v) for k, v in optional if v)

        return result


class BaseFirstClass(Base):
    """First class CIs, officially supported by Coveralls.

    First class CIs are those which Coveralls doesn't require the repo token to be specified. Instead Coveralls will
    use service_name and service_job_id to query the CI for more information about the build.
    """

    @classmethod
    def payload(cls, coverage_result, git_stats_result=None):
        result = super(BaseFirstClass, cls).payload(coverage_result, git_stats_result)

        # Validate.
        if not result.get('service_name') or not result.get('service_job_id'):
            logging.error('Must have both service_job_id and service_name set.')
            logging.debug('service_name: {0}'.format(result.get('service_name')))
            logging.debug('service_job_id: {0}'.format(result.get('service_job_id')))
            raise RuntimeError('Must have both service_job_id and service_name set.')

        return result


class BaseSecondClass(Base):
    """Second class CIs, supported by coveralls_multi_ci using Coverall's generic CI support.

    Second class CIs require the repo token to be sent to Coveralls' API. Additional information helps but is not
    mandatory.
    """
    SERVICE_BRANCH = os.environ.get('CI_BRANCH')
    SERVICE_BUILD_URL = os.environ.get('CI_BUILD_URL')
    SERVICE_NAME = os.environ.get('CI_NAME', Base.SERVICE_NAME)
    SERVICE_NUMBER = os.environ.get('CI_BUILD_NUMBER')
    SERVICE_PULL_REQUEST = os.environ.get('CI_PULL_REQUEST')

    @classmethod
    def payload(cls, coverage_result, git_stats_result=None):
        result = super(BaseSecondClass, cls).payload(coverage_result, git_stats_result)

        # Validate.
        if not result.get('repo_token'):
            logging.error('Must have repo_token set.')
            logging.debug('repo_token: {0}'.format(result.get('repo_token')))
            raise RuntimeError('Must have repo_token set.')

        return result


class TravisCI(BaseFirstClass):
    """http://docs.travis-ci.com/user/ci-environment/#Environment-variables"""
    SERVICE_NAME = 'travis-ci'
    SERVICE_JOB_ID = os.environ.get('TRAVIS_JOB_ID')


class CircleCI(BaseFirstClass):
    """https://circleci.com/docs/environment-variables"""
    SERVICE_NAME = 'circleci'
    SERVICE_NUMBER = os.environ.get('CIRCLE_BUILD_NUM')


class Semaphore(BaseFirstClass):
    """https://semaphoreapp.com/docs/available-environment-variables.html"""
    SERVICE_NAME = 'semaphore'
    SERVICE_NUMBER = os.environ.get('SEMAPHORE_BUILD_NUMBER')


class JenkinsCI(BaseFirstClass):
    """https://wiki.jenkins-ci.org/display/JENKINS/Building+a+software+project"""
    SERVICE_NAME = 'jenkins'
    SERVICE_NUMBER = os.environ.get('BUILD_NUMBER')


class GenericCI(BaseSecondClass):
    """https://github.com/lemurheavy/coveralls-ruby/blob/master/lib/coveralls/configuration.rb#L63"""
    pass


class AppVeyor(BaseSecondClass):
    """http://www.appveyor.com/docs/environment-variables"""
    SERVICE_NAME = 'appveyor'
    SERVICE_BRANCH = os.environ.get('APPVEYOR_REPO_BRANCH')
    SERVICE_BUILD_URL = os.environ.get('APPVEYOR_API_URL')
    SERVICE_JOB_ID = os.environ.get('APPVEYOR_JOB_ID')
    SERVICE_NUMBER = os.environ.get('APPVEYOR_BUILD_NUMBER')
    SERVICE_PULL_REQUEST = os.environ.get('APPVEYOR_PULL_REQUEST_NUMBER')


class Codeship(BaseSecondClass):
    """https://codeship.io/documentation/continuous-integration/set-environment-variables/"""
    SERVICE_NAME = 'codeship'


class Bamboo(BaseSecondClass):
    """https://confluence.atlassian.com/display/BAMBOO/Bamboo+variables"""
    SERVICE_NAME = 'bamboo'
    SERVICE_BRANCH = os.environ.get('bamboo.planRepository.branch')
    SERVICE_BUILD_URL = os.environ.get('bamboo.planRepository.repositoryUrl')
    SERVICE_JOB_ID = os.environ.get('bamboo.buildKey')
    SERVICE_NUMBER = os.environ.get('bamboo.buildNumber')


def git_stats(repo_dir):
    """Generates a dictionary with metadata about the git repo.

    Attempts to resolve branch name if it's HEAD to a tag or branch name if the last commit is referenced by just one
    of either.

    Positional arguments:
    repo_dir -- root directory of the git repository.

    Returns:
    A nested dictionary whose structure matches the JSON data sent to the Coveralls API.
    """
    call = lambda l: subprocess32.check_output(l, cwd=repo_dir).splitlines()

    # Get remotes.
    try:
        gen = (l.split() for l in call(['git', 'remote', '-v']))
        remotes = [dict(name=r[0], url=r[1]) for r in gen if r[2] == '(fetch)']
    except subprocess32.CalledProcessError:
        logging.error('CalledProcessError raised, probably not in a git repo.')
        return dict()

    # Get branches. One commit may be referenced by many branches.
    branches = dict()  # dict(hex=[branch1, branch2, ...])
    for branch in call(['git', 'show-ref', '--heads']):
        branch_name = branch.split(' ', 1)[1][11:]
        gen = (l.split() for l in call(['git', 'reflog', 'show', branch_name, '--pretty=%H %gs']))
        for hex_ in (l[0] for l in gen if 'commit' in l[1]):
            if hex_ not in branches:
                branches[hex_] = set()
            branches[hex_].add(branch_name)

    # Get tags. One commit may be referenced by many tags.
    tags = dict()  # dict(hex=[tag1, tag2, ...])
    for tag in (l.split() for l in call(['git', 'show-ref', '-d']) if 'refs/tags/' in l):
        tag_name = tag[1][10:]
        if tag_name.endswith('^{}'):
            tag_name = tag[1][10:][:-3]
        hex_ = tag[0]
        if hex_ not in tags:
            tags[hex_] = set()
        tags[hex_].add(tag_name)

    # Determine last commit.
    git_log = call(['git', '--no-pager', 'log', '-1', '--pretty=%H%n%aN%n%ae%n%cN%n%ce%n%s'])
    is_detached = call(['git', 'rev-parse', '--symbolic-full-name', '--abbrev-ref', 'HEAD'])[0] == 'HEAD'
    if is_detached and git_log[0] in tags and len(tags[git_log[0]]) == 1:
        branch = next(iter(tags[git_log[0]]))
    elif is_detached and git_log[0] in branches and len(branches[git_log[0]]) == 1:
        branch = next(iter(branches[git_log[0]]))
    else:
        branch = call(['git', 'rev-parse', '--symbolic-full-name', '--abbrev-ref', 'HEAD'])[0]

    # Get metadata.
    head = dict(
        id=git_log[0],
        author_name=git_log[1],
        author_email=git_log[2],
        committer_name=git_log[3],
        committer_email=git_log[4],
        message=git_log[5],
    )

    return dict(head=head, branch=branch, remotes=remotes)


def coverage_report(coverage_file, source_root):
    """Parse coverage file created before this script was executed.

    Looks like the author of Coverage doesn't want us subclassing his classes.
    http://nedbatchelder.com/blog/201409/how_should_i_distribute_coveragepy_alphas.html

    To avoid loading entire project's source code in memory, base64 encoded placeholders are used.

    Raises:
    RuntimeError -- raised after logging to stderr. Caller should just call sys.exit(1).

    Positional arguments:
    coverage_file -- file path to the coverage file.
    source_root -- absolute path to root directory of the project's source code.

    Returns:
    List of dicts, each dict is one file and each dict holds API compatible coverage data.
    """
    if not coverage_file:
        logging.error('No coverage file specified.')
        raise RuntimeError('No coverage file specified.')
    source_root = source_root.rstrip('/') + '/'
    source_files = list()
    logging.debug('Loading coverage file: ' + coverage_file)
    cov = coverage(data_file=coverage_file)
    cov.load()

    for file_path in cov.data.measured_files():
        logging.debug('Found coverage for: {0}'.format(file_path))
        if not os.path.isfile(file_path):
            logging.error('Source file not found: {0}'.format(file_path))
            raise RuntimeError('Source file not found: {0}'.format(file_path))
        if not file_path.startswith(source_root):
            logging.error('Source file path {0} not within source root {1}.'.format(file_path, source_root))
            raise RuntimeError('Source file path {0} not within source root {1}.'.format(file_path, source_root))
        with open(file_path, 'rU') as f:
            logging.debug('Opened {0} for reading.'.format(f.name))
            file_coverage = [None for _ in f]  # List of Nones, same length as the number of lines in the file.
        logging.debug('Closed {0}.'.format(f.name))
        analysis = cov.analysis(file_path)[1:-1]
        fp_relative = file_path[len(source_root):]
        fp_placeholder = '' if not os.path.getsize(file_path) else 'PLACEHOLDER_{0}_'.format(b64encode(file_path))

        for i in analysis[0]:
            file_coverage[i - 1] = 1
        for i in analysis[1]:
            file_coverage[i - 1] = 0

        source_files.append(dict(name=fp_relative, source=fp_placeholder, coverage=file_coverage))

    if not source_files:
        logging.error('No code coverage found.')
        raise RuntimeError('No code coverage found.')

    return source_files


def dump_json_to_disk(payload, target_file):
    """Dumps payload to disk as a JSON. Replaces placeholders with the project's source code.

    Raises:
    RuntimeError -- raised after logging to stderr. Caller should just call sys.exit(1).
    ValueError -- raised if arguments are invalid. Should never happen, treat it as a bug in caller.

    Positional arguments:
    payload -- dict of all data to be sent to the API minus the source code. Placeholders are used instead.
    target_file -- file path to write dumped payload and source code to.

    Returns:
    Number of bytes the target_file is after dumping all data.
    """
    if not payload or not target_file:
        raise ValueError('"payload" or "target_file" invalid.')
    if os.path.exists(target_file):
        logging.error('File already exists: {0}'.format(target_file))
        raise RuntimeError('File already exists: {0}'.format(target_file))
    if not os.path.isdir(os.path.dirname(target_file)):
        logging.error("Parent directory doesn't exist: {0}".format(os.path.dirname(target_file)))
        raise RuntimeError("Parent directory doesn't exist: {0}".format(os.path.dirname(target_file)))

    encoder = json.JSONEncoder()
    payload_string = json.dumps(payload)
    with open(target_file, 'w') as f_target:
        logging.debug('Opened {0} for writing.'.format(f_target.name))
        for segment in _RE_SPLIT.split(payload_string):
            if not segment:
                continue
            if not _RE_SPLIT.match(segment):
                f_target.write(segment)
                continue
            file_path = b64decode(segment[12:-1])
            with open(file_path, 'rU') as f_source:
                logging.debug('Opened {0} for reading.'.format(f_source.name))
                for line in f_source:
                    f_target.write(encoder.encode(line)[1:-1])
            logging.debug('Closed {0}.'.format(f_source.name))
    logging.debug('Closed {0}.'.format(f_target.name))

    byte_size = os.path.getsize(target_file)
    logging.info('Wrote {0} bytes to {1}.'.format(byte_size, target_file))
    return byte_size


def select_ci():
    """Selects the appropriate class and returns it."""
    if 'CI' in os.environ and 'TRAVIS' in os.environ:
        ci_class = TravisCI
    elif 'CI' in os.environ and 'APPVEYOR' in os.environ:
        ci_class = AppVeyor
    elif 'CI' in os.environ and 'CIRCLECI' in os.environ:
        ci_class = CircleCI
    elif 'CI' in os.environ and 'SEMAPHORE' in os.environ:
        ci_class = Semaphore
    elif 'JENKINS_URL' in os.environ:
        ci_class = JenkinsCI
    elif 'CI' in os.environ and os.environ.get('CI_NAME') == 'codeship':
        ci_class = Codeship
    elif 'bamboo.buildNumber' in os.environ:
        ci_class = Bamboo
    else:
        logging.debug('Did not detect an officially supported CI. Resorting to the generic class.')
        ci_class = GenericCI
    return ci_class


def post_to_api(target_file):
    """POSTs the JSON target_file to the Coveralls API.

    Raises:
    RuntimeError -- raised after logging to stderr. Caller should just call sys.exit(1).

    Positional arguments:
    target_file -- JSON string file path to containing dumped payload and source code.
    """
    logging.debug('POSTing to: {0}'.format(API_URL))
    with open(target_file) as f:
        logging.debug('Opened {0} for reading.'.format(f.name))
        response = requests.post(API_URL, files={'json_file': f})
    logging.debug('Closed {0}.'.format(f.name))
    for attr in ('text', 'elapsed', 'headers', 'status_code', 'url'):
        logging.debug('response.{0}: {1}'.format(attr, getattr(response, attr)))
    if not response.ok:
        logging.error('Got HTTP {0} while POSTing, not good.'.format(response.status_code))
        raise RuntimeError('Got HTTP {0} while POSTing, not good.'.format(response.status_code))


def main():
    """Main function called upon script execution."""
    get_dir = lambda d: CWD if d == 'cwd' else os.path.abspath(os.path.expanduser(d))

    # First gather data about the git repo and test coverage.
    repo_dir = get_dir(OPTIONS.get('--git'))
    coverage_file = os.path.abspath(os.path.expanduser(OPTIONS.get('--coverage')))
    source_root = get_dir(OPTIONS.get('--source'))
    logging.info('Gathering git repo and test coverage data.')
    git_stats_result = git_stats(repo_dir)
    try:
        coverage_result = coverage_report(coverage_file, source_root)
    except RuntimeError:
        sys.exit(1)

    # Select class and get the payload.
    ci_class = select_ci()
    logging.info('Selected class: {0}'.format(ci_class.__name__))
    try:
        payload = ci_class.payload(coverage_result=coverage_result, git_stats_result=git_stats_result)
    except RuntimeError:
        sys.exit(1)
    logging.info('Coverage of {0} file(s) found.'.format(len(payload['source_files'])))
    if payload.get('git'):
        logging.info('Git branch/tag: {0}'.format(payload['git']['branch']))
    payload_censored = payload.copy()
    if payload.get('repo_token'):
        payload_censored['repo_token'] = '*' * len(payload['repo_token'])
    logging.debug('Placeholdered payload excluding repo token:\n{0}'.format(payload_censored))

    # Dump payload to file and merge in actual source code.
    target_file = os.path.abspath(os.path.expanduser(OPTIONS.get('--output')))
    try:
        dump_json_to_disk(payload, target_file)
    except RuntimeError:
        sys.exit(1)

    # Ok now we just submit it to the API.
    try:
        post_to_api(target_file)
    except RuntimeError:
        sys.exit(1)

    # Cleanup.
    if not OPTIONS.get('--no-delete'):
        logging.info('Deleting {0}.'.format(target_file))
        os.remove(target_file)
    logging.info('Done.')


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
    fmt = '%(asctime)-15s %(levelname)-8s %(funcName)-17s %(message)s' if OPTIONS.get('--verbose') else '%(message)s'

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
    logging.debug('CWD: {0}'.format(CWD))
    logging.debug('OPTIONS dictionary: \n{0}'.format(OPTIONS))


def entry_point():
    """Entry point for script. Needed for setup.py entry_point definition."""
    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))  # Properly handle Control+C
    if not OPTIONS:
        OPTIONS.update(docopt(__doc__))  # setup.py entry_point scripts don't set __name__ to __main__.
    setup_logging()
    if OPTIONS.get('--version'):
        logging.info('coveralls_multi_ci {0}'.format(__version__))
        sys.exit(0)
    try:
        main()
    except SystemExit as e:
        if e.message != 0:
            logging.critical('!! ABORTING, ERROR OCCURRED !!')
        raise


if __name__ == '__main__':
    entry_point()
