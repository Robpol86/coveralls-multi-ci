from base64 import b64encode
import json
import os
from textwrap import dedent

import pytest

from coveralls_multi_ci import dump_json_to_disk

ROOT = os.path.abspath(os.path.expanduser(os.path.dirname(__file__)))


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
    file_path_sub = b64encode(os.path.join(ROOT, 'sample_project', 'project', 'library', 'sub.py'))
    file_path_main = b64encode(os.path.join(ROOT, 'sample_project', 'project', 'main.py'))
    payload = json.loads(dedent("""\
        {"service_name": "coveralls_multi_ci", "source_files": [{"source": "PLACEHOLDER_%s_", "name": "project/library/
        sub.py", "coverage": [1, 1, 1, 1, null, 0, 0]}, {"source": "", "name": "project/library/__init__.py", "coverage
        ": []}, {"source": "PLACEHOLDER_%s_", "name": "project/main.py", "coverage": [1, null, null, 1, 1, 1, null, 0, 0
        ]}, {"source": "", "name": "project/__init__.py", "coverage": []}]}
    """).replace('\n', '') % (file_path_sub, file_path_main))

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
