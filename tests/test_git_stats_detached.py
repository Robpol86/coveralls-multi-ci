import subprocess

from coveralls_multi_ci import git_stats


def setup_git(repo_dir):
    hashes = dict(master='', feature='', tag='')
    assert 0 == subprocess.check_call(['git', 'init'], cwd=str(repo_dir))
    assert 0 == subprocess.check_call(['git', 'remote', 'add', 'origin', 'http://localhost/git.git'], cwd=str(repo_dir))
    assert 0 == subprocess.check_call(['git', 'config', '--local', 'user.name', 'MrCommit'], cwd=str(repo_dir))
    assert 0 == subprocess.check_call(['git', 'config', '--local', 'user.email', 'mc@aol.com'], cwd=str(repo_dir))
    repo_dir.join('test.txt').ensure(file=True)
    assert 0 == subprocess.check_call(['git', 'add', '.'], cwd=str(repo_dir))
    assert 0 == subprocess.check_call(['git', 'commit', '-m', 'Committing empty file.', '--author',
                                       'MrsAuthor <ma@aol.com>'], cwd=str(repo_dir))
    hashes['master'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=str(repo_dir)).strip()

    assert 0 == subprocess.check_call(['git', 'checkout', '-b', 'feature'], cwd=str(repo_dir))
    repo_dir.join('test.txt').write('test')
    assert 0 == subprocess.check_call(['git', 'add', '.'], cwd=str(repo_dir))
    assert 0 == subprocess.check_call(['git', 'commit', '-m', 'Wrote to file.'], cwd=str(repo_dir))
    hashes['feature'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=str(repo_dir)).strip()

    assert 0 == subprocess.check_call(['git', 'checkout', 'master'], cwd=str(repo_dir))
    assert 0 == subprocess.check_call(['git', 'tag', '-a', 'v1.0', '-m', 'First Version'], cwd=str(repo_dir))
    hashes['tag'] = subprocess.check_output(['git', 'rev-parse', 'v1.0'], cwd=str(repo_dir)).strip()

    assert all(hashes.values())
    assert 3 == len(set(hashes.values()))
    return hashes


def test_master(tmpdir):
    repo_dir = tmpdir.join('project').ensure(dir=True)
    hex_sha = setup_git(repo_dir)['master']
    assert 0 == subprocess.check_call(['git', 'checkout', '-qf', hex_sha], cwd=str(repo_dir))

    actual = git_stats(str(repo_dir))
    expected = dict(
        branch='master',
        remotes=[dict(name='origin', url='http://localhost/git.git'), ],
        head=dict(
            id=hex_sha,
            author_name='MrsAuthor',
            author_email='ma@aol.com',
            committer_name='MrCommit',
            committer_email='mc@aol.com',
            message='Committing empty file.'
        )
    )
    assert expected == actual


def test_feature_branch(tmpdir):
    repo_dir = tmpdir.join('project').ensure(dir=True)
    hex_sha = setup_git(repo_dir)['feature']
    assert 0 == subprocess.check_call(['git', 'checkout', '-qf', hex_sha], cwd=str(repo_dir))

    actual = git_stats(str(repo_dir))
    expected = dict(
        branch='feature',
        remotes=[dict(name='origin', url='http://localhost/git.git'), ],
        head=dict(
            id=hex_sha,
            author_name='MrCommit',
            author_email='mc@aol.com',
            committer_name='MrCommit',
            committer_email='mc@aol.com',
            message='Wrote to file.'
        )
    )
    assert expected == actual


def test_tag(tmpdir):
    repo_dir = tmpdir.join('project').ensure(dir=True)
    hex_sha = setup_git(repo_dir)['tag']
    assert 0 == subprocess.check_call(['git', 'checkout', '-qf', hex_sha], cwd=str(repo_dir))

    actual = git_stats(str(repo_dir))
    expected = dict(
        branch='v1.0',
        remotes=[dict(name='origin', url='http://localhost/git.git'), ],
        head=dict(
            id=hex_sha,
            author_name='MrsAuthor',
            author_email='ma@aol.com',
            committer_name='MrCommit',
            committer_email='mc@aol.com',
            message='Committing empty file.'
        )
    )
    assert expected == actual


def test_pull_request():
    pass  # TODO
