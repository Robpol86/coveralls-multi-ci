from coveralls_multi_ci import coverage_report


def test_no_file_coverage(tmpdir):
    coverage_file = tmpdir.join('coverage')
    assert [] == coverage_report('')
    assert [] == coverage_report(str(coverage_file))  # File does not exist.
    coverage_file.ensure(file=True)
    assert [] == coverage_report(str(coverage_file))  # Empty file.


def test_no_file_source():
    pass


def test_no_coverage():
    pass


def test_partial_coverage():
    pass


def test_full_coverage():
    pass
