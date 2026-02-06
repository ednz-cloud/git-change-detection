import pytest
from git import InvalidGitRepositoryError, BadName

import git_change_detection.utils.git as git_utils


@pytest.fixture
def mock_repo(mocker):
    """Fixture to mock a Repo object."""
    return mocker.patch("git_change_detection.utils.git.Repo")


@pytest.mark.parametrize(
    "first, last, setup_side_effect, expected_msg",
    [
        ("a", "b", InvalidGitRepositoryError, "not a valid Git repository"),
        ("missing", "b", None, "Commit 'missing' not found"),
        ("a", "missing", None, "Commit 'missing' not found"),
    ],
)
def test_get_changed_files_exceptions(first, last, setup_side_effect, expected_msg, mock_repo):
    if setup_side_effect is InvalidGitRepositoryError:
        mock_repo.side_effect = InvalidGitRepositoryError
    else:
        repo = mock_repo.return_value

        def fake_commit(arg):
            if arg in ("missing", "missing"):
                raise BadName
            return object()

        repo.commit.side_effect = fake_commit

    with pytest.raises(RuntimeError, match=expected_msg):
        git_utils.get_changed_files(first, last, repo_path=None)


@pytest.mark.parametrize(
    "diff_entries, expected_files",
    [
        ([type("D", (), {"a_path": "file1.txt", "b_path": None})()], ["file1.txt"]),
        ([type("D", (), {"a_path": None, "b_path": "file2.txt"})()], ["file2.txt"]),
        (
            [type("D", (), {"a_path": "old.txt", "b_path": "new.txt"})()],
            ["old.txt", "new.txt"],
        ),
        ([], []),
        (
            [
                type("D", (), {"a_path": "f1", "b_path": "f1_new"})(),
                type("D", (), {"a_path": "f2", "b_path": None})(),
            ],
            ["f1", "f1_new", "f2"],
        ),
    ],
)
def test_get_changed_files_diff_variants(diff_entries, expected_files, mock_repo, mocker):
    repo = mock_repo.return_value

    commit_a = mocker.Mock()
    commit_b = mocker.Mock()
    commit_a.diff.return_value = diff_entries

    def fake_commit(c):
        return commit_a if c == "a" else commit_b

    repo.commit.side_effect = fake_commit

    files = git_utils.get_changed_files("a", "b")
    assert sorted(files) == sorted(expected_files)
