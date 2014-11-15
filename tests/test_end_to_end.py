from datetime import datetime
import json
import os

from httpretty import POST, register_uri
import pytest
from pytest_httpretty import last_request

import coveralls_multi_ci

ROOT = os.path.abspath(os.path.dirname(__file__))


def execute(environ, options):
    original_environ = os.environ.copy()
    original_options = coveralls_multi_ci.OPTIONS.copy()
    os.environ.clear()
    os.environ.update(environ)
    reload(coveralls_multi_ci)

    coveralls_multi_ci.OPTIONS.update(original_options)
    coveralls_multi_ci.OPTIONS.update({
        '--coverage': os.path.join(ROOT, 'sample_project', 'coverage_project_full'),
        '--source': os.path.join(ROOT, 'sample_project'),
    })
    coveralls_multi_ci.OPTIONS.update(options)
    coveralls_multi_ci.main()

    os.environ.clear()
    os.environ.update(original_environ)


def common_verify(request, json_payload):
    assert 'POST' == request.method
    assert request.headers['content-type'].startswith('multipart/form-data; boundary=')
    expected = 'Content-Disposition: form-data; name="json_file"; filename="coveralls_multi_ci_payload.txt"'
    assert expected == request.body.splitlines()[1]
    assert ['branch', 'head', 'remotes'] == sorted(json_payload['git'].keys())
    assert json_payload['run_at'].endswith(' +0000')
    assert isinstance(datetime.strptime(json_payload['run_at'][:-6], '%Y-%m-%d %H:%M:%S'), datetime)
    assert 4 == len(json_payload['source_files'])


@pytest.mark.httpretty
def test_errors():
    register_uri(POST, coveralls_multi_ci.API_URL)

    with pytest.raises(SystemExit):
        execute(dict(), dict())


@pytest.mark.httpretty
def test_generic_minimum():
    register_uri(POST, coveralls_multi_ci.API_URL)
    execute(dict(COVERALLS_REPO_TOKEN='abc'), dict())
    request = last_request()
    json_payload = json.loads(request.body.splitlines()[3])
    common_verify(request, json_payload)
    assert ['git', 'repo_token', 'run_at', 'service_name', 'source_files'] == sorted(json_payload.keys())

    assert 'abc' == json_payload['repo_token']
    assert 'coveralls_multi_ci' == json_payload['service_name']


@pytest.mark.httpretty
def test_generic_maximum():
    register_uri(POST, coveralls_multi_ci.API_URL)
    execute(dict(COVERALLS_REPO_TOKEN='def', CI_NAME='test_run', CI_BUILD_NUMBER='9', CI_BUILD_URL='http://localhost/9',
                 CI_BRANCH='feature2', CI_PULL_REQUEST='1'), dict())
    request = last_request()
    json_payload = json.loads(request.body.splitlines()[3])
    common_verify(request, json_payload)
    expected = ['git', 'repo_token', 'run_at', 'service_branch', 'service_build_url', 'service_name', 'service_number',
                'service_pull_request', 'source_files']
    assert expected == sorted(json_payload.keys())

    assert 'def' == json_payload['repo_token']
    assert 'feature2' == json_payload['service_branch']
    assert 'http://localhost/9' == json_payload['service_build_url']
    assert 'test_run' == json_payload['service_name']
    assert '9' == json_payload['service_number']
    assert '1' == json_payload['service_pull_request']
