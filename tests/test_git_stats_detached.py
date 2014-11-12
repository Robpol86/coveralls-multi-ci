import subprocess

from coveralls_multi_ci import git_stats


def test_master(repo_dir, hashes):
    hex_sha = hashes['master']
    assert 0 == subprocess.check_call(['git', 'checkout', '-qf', hex_sha], cwd=repo_dir)

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


def test_feature_branch(repo_dir, hashes):
    hex_sha = hashes['feature']
    assert 0 == subprocess.check_call(['git', 'checkout', '-qf', hex_sha], cwd=repo_dir)

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


def test_tag_annotated(repo_dir, hashes):
    hex_sha = hashes['tag_annotated']
    assert 0 == subprocess.check_call(['git', 'checkout', '-qf', hex_sha], cwd=repo_dir)

    actual = git_stats(repo_dir)
    expected = dict(
        branch='v1.0',
        remotes=[dict(name='origin', url='http://localhost/git.git'), ],
        head=dict(
            id=hex_sha,
            author_name='MrCommit',
            author_email='mc@aol.com',
            committer_name='MrCommit',
            committer_email='mc@aol.com',
            message='Wrote to file2.'
        )
    )
    assert expected == actual


def test_tag_light(repo_dir, hashes):
    hex_sha = hashes['tag_light']
    assert 0 == subprocess.check_call(['git', 'checkout', '-qf', hex_sha], cwd=repo_dir)

    actual = git_stats(repo_dir)
    expected = dict(
        branch='v1.0l',
        remotes=[dict(name='origin', url='http://localhost/git.git'), ],
        head=dict(
            id=hex_sha,
            author_name='MrCommit',
            author_email='mc@aol.com',
            committer_name='MrCommit',
            committer_email='mc@aol.com',
            message='Wrote to file3.'
        )
    )
    assert expected == actual
