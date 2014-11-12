import os

from coveralls_multi_ci import coverage_report

CWD = os.path.abspath(os.path.expanduser(os.path.dirname(__file__)))


def test_no_file_coverage(tmpdir):
    coverage_file = tmpdir.join('coverage')
    assert [] == coverage_report('', '')
    assert [] == coverage_report(str(coverage_file), '')  # File does not exist.
    coverage_file.ensure(file=True)
    assert [] == coverage_report(str(coverage_file), '')  # Empty file.


def test_partial_coverage():
    coverage_file = os.path.join(CWD, 'sample_project', 'coverage_script_partial')
    # TODO
    coverage_file = os.path.join(CWD, 'sample_project', 'coverage_project_partial')
    # TODO


def test_full_coverage():
    pass
