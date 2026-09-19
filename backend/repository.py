from pathlib import Path


SUPPORTED_EXTENSIONS = {
    ".py",
}


def find_code_files(repo_path: str) -> list[str]:
    """
    Find supported source-code files inside a repository.
    """
    root = Path(repo_path)

    if not root.exists():
        return []

    files = []

    for path in root.rglob("*"):
        if (
            path.is_file()
            and path.suffix in SUPPORTED_EXTENSIONS
            and ".git" not in path.parts
            and "venv" not in path.parts
            and "__pycache__" not in path.parts
        ):
            files.append(str(path))

    return files


def read_code_file(file_path: str) -> str:
    """
    Read a source-code file.
    """
    return Path(file_path).read_text(encoding="utf-8")