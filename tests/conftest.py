import os
import shutil
import subprocess
import tempfile

import pytest

from coveralls_multi_ci import OPTIONS, setup_logging


OPTIONS.update({
    '--coverage': '.coverage',
    '--git': 'cwd',
    '--help': False,
    '--no-delete': False,
    '--output': 'coveralls_multi_ci_payload.txt',
    '--quiet': False,
    '--source': 'cwd',
    '--verbose': True,
    '--version': False,
    'submit': True
})
setup_logging()


@pytest.fixture(scope='module')
def repo_dir(request):
    rd = tempfile.mkdtemp()
    request.addfinalizer(lambda: shutil.rmtree(rd))

    assert 0 == subprocess.check_call(['git', 'init'], cwd=rd)
    assert 0 == subprocess.check_call(['git', 'remote', 'add', 'origin', 'http://localhost/git.git'], cwd=rd)
    assert 0 == subprocess.check_call(['git', 'config', '--local', 'user.name', 'MrCommit'], cwd=rd)
    assert 0 == subprocess.check_call(['git', 'config', '--local', 'user.email', 'mc@aol.com'], cwd=rd)
    with open(os.path.join(rd, 'test.txt'), 'a'):
        pass
    assert 0 == subprocess.check_call(['git', 'add', 'test.txt'], cwd=rd)
    assert 0 == subprocess.check_call(['git', 'commit', '-m', 'Committing empty file.', '--author',
                                       'MrsAuthor <ma@aol.com>'], cwd=rd)

    return rd


@pytest.fixture(scope='module')
def hashes(repo_dir):
    hashes_ = dict(master='', feature='', tag_annotated='', tag_light='')
    hashes_['master'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo_dir).strip()

    assert 0 == subprocess.check_call(['git', 'checkout', '-b', 'feature'], cwd=repo_dir)
    with open(os.path.join(repo_dir, 'test.txt'), 'a') as f:
        f.write('test')
    assert 0 == subprocess.check_call(['git', 'add', 'test.txt'], cwd=repo_dir)
    assert 0 == subprocess.check_call(['git', 'commit', '-m', 'Wrote to file.'], cwd=repo_dir)
    hashes_['feature'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo_dir).strip()

    assert 0 == subprocess.check_call(['git', 'checkout', 'master'], cwd=repo_dir)
    with open(os.path.join(repo_dir, 'test.txt'), 'a') as f:
        f.write('test2')
    assert 0 == subprocess.check_call(['git', 'add', 'test.txt'], cwd=repo_dir)
    assert 0 == subprocess.check_call(['git', 'commit', '-m', 'Wrote to file2.'], cwd=repo_dir)
    assert 0 == subprocess.check_call(['git', 'tag', '-a', 'v1.0', '-m', 'First Version'], cwd=repo_dir)
    hashes_['tag_annotated'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo_dir).strip()

    with open(os.path.join(repo_dir, 'test.txt'), 'a') as f:
        f.write('test3')
    assert 0 == subprocess.check_call(['git', 'add', 'test.txt'], cwd=repo_dir)
    assert 0 == subprocess.check_call(['git', 'commit', '-m', 'Wrote to file3.'], cwd=repo_dir)
    assert 0 == subprocess.check_call(['git', 'tag', 'v1.0l'], cwd=repo_dir)
    hashes_['tag_light'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo_dir).strip()

    assert all(hashes_.values())
    assert 4 == len(set(hashes_.values()))
    return hashes_


@pytest.fixture(autouse=True, scope='session')
def create_coverage(request):
    sample_project_root = os.path.join(os.path.abspath(os.path.expanduser(os.path.dirname(__file__))), 'sample_project')
    environ = os.environ.copy()
    environ.pop('COV_CORE_DATA_FILE', None)
    environ.update(dict(PYTHONPATH='.'))
    coverage = os.path.join(sample_project_root, '.coverage')
    pre = ['py.test', '--cov-report', 'term-missing', '--cov']

    def fin():
        os.remove(os.path.join(sample_project_root, 'coverage_script_partial'))
        os.remove(os.path.join(sample_project_root, 'coverage_script_full'))
        os.remove(os.path.join(sample_project_root, 'coverage_project_partial'))
        os.remove(os.path.join(sample_project_root, 'coverage_project_full'))
    request.addfinalizer(fin)

    # coverage_script_partial
    subprocess.check_call(pre + ['script', 'tests/test_script_partial.py'], cwd=sample_project_root, env=environ)
    os.rename(coverage, os.path.join(sample_project_root, 'coverage_script_partial'))

    # coverage_script_full
    subprocess.check_call(pre + ['script', 'tests/test_script_full.py'], cwd=sample_project_root, env=environ)
    os.rename(coverage, os.path.join(sample_project_root, 'coverage_script_full'))

    # coverage_project_partial
    subprocess.check_call(pre + ['project', 'tests/test_project_partial.py'], cwd=sample_project_root, env=environ)
    os.rename(coverage, os.path.join(sample_project_root, 'coverage_project_partial'))

    # coverage_project_full
    subprocess.check_call(pre + ['project', 'tests/test_project_full.py'], cwd=sample_project_root, env=environ)
    os.rename(coverage, os.path.join(sample_project_root, 'coverage_project_full'))