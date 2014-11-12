import os
import subprocess

from coveralls_multi_ci import git_stats


def test_master(repo_dir):
    hex_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo_dir).strip()

    actual = git_stats(repo_dir)
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


def test_feature_branch(repo_dir):
    assert 0 == subprocess.check_call(['git', 'checkout', '-b', 'feature'], cwd=repo_dir)
    with open(os.path.join(repo_dir, 'test.txt'), 'a') as f:
        f.write('test')
    assert 0 == subprocess.check_call(['git', 'add', 'test.txt'], cwd=repo_dir)
    assert 0 == subprocess.check_call(['git', 'commit', '-m', 'Wrote to file.'], cwd=repo_dir)
    hex_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo_dir).strip()

    actual = git_stats(repo_dir)
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