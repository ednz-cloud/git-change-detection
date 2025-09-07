from pathlib import Path
from git import Repo, InvalidGitRepositoryError, BadName, NoSuchPathError


def get_changed_files(
    first_commit: str, last_commit: str, repo_path: Path | None = None
) -> list[str]:
    """
    Return a list of files changed between two commits in a Git repo.

    Args:
        first_commit: The base commit (older).
        last_commit: The target commit (newer).
        repo_path: Path to the repository (defaults to current working dir).

    Returns:
        List of changed file paths (as strings, relative to repo root).
    """
    repo_path = Path(repo_path or Path.cwd())

    try:
        repo = Repo(repo_path, search_parent_directories=True)
    except (InvalidGitRepositoryError, NoSuchPathError) as e:
        raise RuntimeError(f"{repo_path} is not a valid Git repository.") from e

    try:
        commit_a = repo.commit(first_commit)
    except BadName as e:
        raise RuntimeError(f"Commit '{first_commit}' not found in repository.") from e

    try:
        commit_b = repo.commit(last_commit)
    except BadName as e:
        raise RuntimeError(f"Commit '{last_commit}' not found in repository.") from e

    diff = commit_a.diff(commit_b, paths=None, create_patch=False)

    changed_files = set()
    for d in diff:
        if d.a_path:
            changed_files.add(d.a_path)
        if d.b_path:
            changed_files.add(d.b_path)

    return sorted(changed_files)
