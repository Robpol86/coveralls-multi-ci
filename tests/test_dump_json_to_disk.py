import json
from textwrap import dedent

import pytest

from coveralls_multi_ci import dump_json_to_disk


def test_errors(tmpdir):
    with pytest.raises(ValueError):
        dump_json_to_disk(dict(), '')

    with pytest.raises(ValueError):
        dump_json_to_disk(dict(service_name='coveralls_multi_ci'), '')

    with pytest.raises(ValueError):
        dump_json_to_disk(dict(), '.coverage')

    target_file = tmpdir.join('dir').join('coveralls_multi_ci_payload.txt')
    with pytest.raises(RuntimeError):
        dump_json_to_disk(dict(service_name='coveralls_multi_ci'), str(target_file))  # Parent directory doesn't exist.

    target_file.ensure(file=True)
    with pytest.raises(RuntimeError):
        dump_json_to_disk(dict(service_name='coveralls_multi_ci'), str(target_file))  # File already exists.


def test(tmpdir):
    target_file = tmpdir.join('coveralls_multi_ci_payload.txt')
    payload = json.loads(dedent("""\
        {"service_name": "coveralls_multi_ci", "source_files": [{"source": "PLACEHOLDER_L1VzZXJzL3JvYnBvbDg2L3dvcmtzcG
        FjZS9jb3ZlcmFsbHMtbXVsdGktY2kvdGVzdHMvc2FtcGxlX3Byb2plY3QvcHJvamVjdC9saWJyYXJ5L3N1Yi5weQ==_", "name": "project/
        library/sub.py", "coverage": [1, 1, 1, 1, null, 0, 0]}, {"source": "", "name": "proje
        ct/library/__init__.py", "coverage": []}, {"source": "PLACEHOLDER_L1VzZXJzL3JvYnBvbDg2L3dvcmtzcGFjZS9jb3ZlcmFsb
        HMtbXVsdGktY2kvdGVzdHMvc2FtcGxlX3Byb2plY3QvcHJvamVjdC9tYWluLnB5_", "name": "project/main.py", "coverage": [1, n
        ull, null, 1, 1, 1, null, 0, 0]}, {"source": "", "name": "project/__init__.py", "coverage": [
        ]}]}
    """).replace('\n', ''))

    byte_size = dump_json_to_disk(payload=payload, target_file=str(target_file))
    assert 600 <= byte_size <= 700

    actual = json.loads(target_file.read())
    expected = dict(
        service_name='coveralls_multi_ci',
        source_files=[
            dict(
                name='project/library/sub.py',
                coverage=[1, 1, 1, 1, None, 0, 0],
                source=('def sub_func(condition):\n    if condition:\n        x = 5 + 5\n        return x\n    else:\n'
                        '        x2 = 5 - 5\n        return x2\n')
            ),
            dict(
                name='project/library/__init__.py',
                coverage=[],
                source=''
            ),
            dict(
                name='project/main.py',
                coverage=[1, None, None, 1, 1, 1, None, 0, 0],
                source=('from project.library import sub\n\n\ndef main(condition):\n    if condition:\n        return '
                        'sub.sub_func(condition)\n    else:\n        y = 0\n        return sub.sub_func(y)\n')
            ),
            dict(
                name='project/__init__.py',
                coverage=[],
                source=''
            ),
        ]
    )
    assert expected == actual
