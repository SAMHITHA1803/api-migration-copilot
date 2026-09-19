from pathlib import Path
from datetime import datetime
import shutil

from git import Repo


PROTECTED_BRANCHES = {
    "main",
    "master"
}


def find_git_repository(path: Path):

    current = path.resolve()

    if current.is_file():
        current = current.parent

    for directory in [
        current,
        *current.parents
    ]:

        if (directory / ".git").exists():

            try:
                return Repo(directory)

            except Exception:
                return None

    return None


def apply_migration(
    file_path: str,
    migrated_code: str
) -> dict:

    path = Path(file_path)

    if not path.exists():

        return {
            "success": False,
            "file": file_path,
            "message": "File does not exist."
        }

    try:

        repo = find_git_repository(path)

        if repo is not None:

            current_branch = repo.active_branch.name

            # ---------------------------------------------
            # HARD SAFETY CHECK
            # ---------------------------------------------

            if current_branch in PROTECTED_BRANCHES:

                return {
                    "success": False,
                    "file": file_path,
                    "message": (
                        f"Migration blocked. "
                        f"Current branch '{current_branch}' "
                        f"is protected."
                    )
                }

        # ---------------------------------------------
        # Backup
        # ---------------------------------------------

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        backup_path = path.with_name(
            f"{path.stem}.backup_{timestamp}{path.suffix}"
        )

        shutil.copy2(
            path,
            backup_path
        )

        # ---------------------------------------------
        # Apply migration
        # ---------------------------------------------

        path.write_text(
            migrated_code,
            encoding="utf-8"
        )

        return {
            "success": True,
            "file": path.name,
            "file_path": str(path),
            "backup_path": str(backup_path),
            "branch": (
                repo.active_branch.name
                if repo is not None
                else None
            ),
            "message": (
                "Migration applied successfully. "
                "Original file backed up."
            )
        }

    except Exception as e:

        return {
            "success": False,
            "file": file_path,
            "message": str(e)
        }