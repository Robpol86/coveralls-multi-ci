import os

from coveralls_multi_ci import coverage_report

CWD = os.path.abspath(os.path.expanduser(os.path.dirname(__file__)))


def test_no_file(tmpdir):
    coverage_file = tmpdir.join('coverage')
    assert list() == coverage_report(str(coverage_file), '')  # File does not exist.
    coverage_file.ensure(file=True)
    assert list() == coverage_report(str(coverage_file), '')  # Empty file.


def test_coverage_script_partial():
    coverage_file = os.path.join(CWD, 'sample_project', 'coverage_script_partial')
    source_root = os.path.join(CWD, 'sample_project')
    coverage_result = coverage_report(coverage_file, source_root)

    assert 1 == len(coverage_result)
    assert 'script.py' == coverage_result[0]['name']
    assert len(coverage_result[0]['source'].splitlines()) == len(coverage_result[0]['coverage'])
    assert 0 in coverage_result[0]['coverage']
    assert 1 in coverage_result[0]['coverage']


def test_coverage_script_full():
    coverage_file = os.path.join(CWD, 'sample_project', 'coverage_script_full')
    source_root = os.path.join(CWD, 'sample_project')
    coverage_result = coverage_report(coverage_file, source_root)

    assert 1 == len(coverage_result)
    assert 'script.py' == coverage_result[0]['name']
    assert len(coverage_result[0]['source'].splitlines()) == len(coverage_result[0]['coverage'])
    assert 0 not in coverage_result[0]['coverage']
    assert 1 in coverage_result[0]['coverage']


def test_coverage_project_partial():
    coverage_file = os.path.join(CWD, 'sample_project', 'coverage_project_partial')
    source_root = os.path.join(CWD, 'sample_project')
    coverage_result = coverage_report(coverage_file, source_root)

    assert 4 == len(coverage_result)
    expected = ['project/__init__.py', 'project/library/__init__.py', 'project/library/sub.py', 'project/main.py']
    assert expected == sorted(i['name'] for i in coverage_result)
    for coverage in coverage_result:
        if coverage['name'].endswith('__init__.py'):
            assert 0 == len(coverage['coverage'])
        else:
            assert len(coverage['source'].splitlines()) == len(coverage['coverage'])
            assert 0 in coverage['coverage']
            assert 1 in coverage['coverage']


def test_coverage_project_full():
    coverage_file = os.path.join(CWD, 'sample_project', 'coverage_project_full')
    source_root = os.path.join(CWD, 'sample_project')
    coverage_result = coverage_report(coverage_file, source_root)

    assert 4 == len(coverage_result)
    expected = ['project/__init__.py', 'project/library/__init__.py', 'project/library/sub.py', 'project/main.py']
    assert expected == sorted(i['name'] for i in coverage_result)
    for coverage in coverage_result:
        if coverage['name'].endswith('__init__.py'):
            assert 0 == len(coverage['coverage'])
        else:
            assert len(coverage['source'].splitlines()) == len(coverage['coverage'])
            assert 0 not in coverage['coverage']
            assert 1 in coverage['coverage']
