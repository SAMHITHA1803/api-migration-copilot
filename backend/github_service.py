import os
import base64
import shutil
import stat
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from git import Repo
import requests


# =========================================================
# CONFIG
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[1]

load_dotenv(BASE_DIR / ".env")

WORKSPACE_ROOT = BASE_DIR / "workspace"
WORKSPACE_ROOT.mkdir(exist_ok=True)


# =========================================================
# HELPERS
# =========================================================

def sanitize_error(message: str) -> str:

    token = os.getenv("GITHUB_TOKEN")

    if token:
        message = message.replace(
            token,
            "***TOKEN***"
        )

    return message


def github_headers():

    token = os.getenv("GITHUB_TOKEN")

    if not token:
        return None

    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def parse_github_repo_url(repo_url: str):

    clean = repo_url.rstrip("/")

    if clean.endswith(".git"):
        clean = clean[:-4]

    parts = clean.split("/")

    return parts[-2], parts[-1]


def get_repo_info(repo_url):

    owner, repo = parse_github_repo_url(repo_url)

    headers = github_headers()

    r = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}",
        headers=headers,
        timeout=30
    )

    if r.status_code != 200:
        raise Exception(r.text)

    return r.json()


# =========================================================
# WINDOWS SAFE FILE DELETION
# =========================================================

def remove_readonly(func, path, exc_info):

    try:
        os.chmod(
            path,
            stat.S_IWRITE
        )

        func(path)

    except Exception:
        raise


# =========================================================
# CLEAR WORKSPACE
# =========================================================

def clear_workspace_root():

    if not WORKSPACE_ROOT.exists():

        WORKSPACE_ROOT.mkdir(
            parents=True,
            exist_ok=True
        )

        return False

    cleared_anything = False

    print("\n" + "=" * 70)
    print("CLEARING WORKSPACE")
    print("=" * 70)
    print(f"Workspace: {WORKSPACE_ROOT}")

    for child in WORKSPACE_ROOT.iterdir():

        print(f"Removing: {child}")

        if child.is_dir():

            shutil.rmtree(
                child,
                onerror=remove_readonly
            )

        else:

            try:

                child.unlink()

            except PermissionError:

                os.chmod(
                    child,
                    stat.S_IWRITE
                )

                child.unlink()

        cleared_anything = True

    print("Workspace cleared.")
    print("=" * 70 + "\n")

    return cleared_anything


# =========================================================
# CLONE
# =========================================================

def clone_repository(repo_url: str):

    try:

        repo_name = (
            repo_url
            .rstrip("/")
            .split("/")[-1]
        )

        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]

        repo_path = (
            WORKSPACE_ROOT /
            repo_name
        )

        print("\n" + "=" * 70)
        print("CLONING REPOSITORY")
        print("=" * 70)
        print(
            f"Repository path: "
            f"{repo_path}"
        )

        # -------------------------------------------------
        # The workspace should already have been cleared
        # before the agent starts.
        # -------------------------------------------------

        if repo_path.exists():

            print(
                "WARNING: Repository path "
                "still exists after workspace cleanup."
            )

            print(
                "Removing it before cloning..."
            )

            shutil.rmtree(
                repo_path,
                onerror=remove_readonly
            )

        # -------------------------------------------------
        # Clone fresh repository
        # -------------------------------------------------

        print(
            "Cloning fresh repository..."
        )

        Repo.clone_from(
            repo_url,
            repo_path
        )

        print(
            "Fresh repository cloned."
        )

        print("=" * 70 + "\n")

        return {
            "success": True,
            "repo_url": repo_url,
            "local_path": str(repo_path),
            "reused": False
        }

    except Exception as e:

        print("\n" + "=" * 70)
        print(
            "REPOSITORY CLONE ERROR"
        )
        print("=" * 70)

        print(str(e))

        print("=" * 70 + "\n")

        return {
            "success": False,
            "error": sanitize_error(
                str(e)
            )
        }


# =========================================================
# BRANCH
# =========================================================

def create_migration_branch(
    repo_path: str,
    branch_name: str = "api-migration"
):

    try:

        repo = Repo(repo_path)

        base = repo.active_branch.name

        timestamp = (
            datetime.now()
            .strftime("%Y%m%d-%H%M%S")
        )

        branch_name = (
            f"{branch_name}-{timestamp}"
        )

        branch = repo.create_head(
            branch_name
        )

        branch.checkout()

        return {
            "success": True,
            "branch_name": branch_name,
            "base_branch": base,
            "repository": repo_path
        }

    except Exception as e:

        return {
            "success": False,
            "message": sanitize_error(
                str(e)
            )
        }


# =========================================================
# COMMIT
# =========================================================

def commit_migration(
    repo_path: str,
    commit_message: str
):

    try:

        repo = Repo(repo_path)

        repo.git.add("-u")

        if not repo.is_dirty(
            index=True
        ):

            return {
                "success": False,
                "message": (
                    "No changes to commit."
                )
            }

        commit = repo.index.commit(
            commit_message
        )

        return {
            "success": True,
            "commit_hash": commit.hexsha,
            "branch": repo.active_branch.name
        }

    except Exception as e:

        return {
            "success": False,
            "message": sanitize_error(
                str(e)
            )
        }


# =========================================================
# API PUBLISH BRANCH
# =========================================================

def push_branch(
    repo_path: str,
    branch_name: str
):

    try:

        repo = Repo(repo_path)

        remote_url = next(
            repo.remote("origin").urls
        )

        owner, repo_name = (
            parse_github_repo_url(
                remote_url
            )
        )

        headers = github_headers()

        if headers is None:

            return {
                "success": False,
                "message": (
                    "GITHUB_TOKEN missing."
                )
            }

        # ---------------------------------------------
        # Repository information
        # ---------------------------------------------

        info = requests.get(
            f"https://api.github.com/repos/"
            f"{owner}/{repo_name}",
            headers=headers,
            timeout=30
        )

        if info.status_code != 200:
            raise Exception(
                info.text
            )

        default_branch = (
            info.json()["default_branch"]
        )

        # ---------------------------------------------
        # Get default branch SHA
        # ---------------------------------------------

        ref = requests.get(
            f"https://api.github.com/repos/"
            f"{owner}/{repo_name}/git/ref/"
            f"heads/{default_branch}",
            headers=headers,
            timeout=30
        )

        if ref.status_code != 200:
            raise Exception(
                ref.text
            )

        base_commit_sha = (
            ref.json()["object"]["sha"]
        )

        # ---------------------------------------------
        # Create remote branch
        # ---------------------------------------------

        create_ref = requests.post(
            f"https://api.github.com/repos/"
            f"{owner}/{repo_name}/git/refs",
            headers=headers,
            json={
                "ref": (
                    f"refs/heads/"
                    f"{branch_name}"
                ),
                "sha": base_commit_sha
            },
            timeout=30
        )

        if create_ref.status_code not in [
            201,
            422
        ]:

            raise Exception(
                create_ref.text
            )

        # ---------------------------------------------
        # Find changed files locally
        # ---------------------------------------------

        changed_files = repo.git.diff(
            f"{default_branch}...HEAD",
            "--name-only"
        ).splitlines()

        if not changed_files:

            return {
                "success": False,
                "message": (
                    "No changed files found."
                )
            }

        # ---------------------------------------------
        # Upload each changed file
        # ---------------------------------------------

        uploaded = []

        for file in changed_files:

            local_file = (
                Path(repo_path) /
                file
            )

            if not local_file.exists():
                continue

            content = (
                local_file
                .read_bytes()
            )

            encoded = (
                base64
                .b64encode(content)
                .decode()
            )

            # Get existing SHA if file exists
            existing = requests.get(
                f"https://api.github.com/repos/"
                f"{owner}/{repo_name}/contents/"
                f"{file}",
                headers=headers,
                params={
                    "ref": branch_name
                },
                timeout=30
            )

            payload = {
                "message": (
                    f"API Migration: "
                    f"update {file}"
                ),
                "content": encoded,
                "branch": branch_name
            }

            if existing.status_code == 200:

                payload["sha"] = (
                    existing.json()["sha"]
                )

            update = requests.put(
                f"https://api.github.com/repos/"
                f"{owner}/{repo_name}/contents/"
                f"{file}",
                headers=headers,
                json=payload,
                timeout=30
            )

            if update.status_code not in [
                200,
                201
            ]:

                raise Exception(
                    update.text
                )

            uploaded.append(file)

        return {
            "success": True,
            "branch_name": branch_name,
            "uploaded_files": uploaded,
            "message": (
                "Branch published using "
                "GitHub API."
            )
        }

    except Exception as e:

        return {
            "success": False,
            "message": sanitize_error(
                str(e)
            )
        }


# =========================================================
# CREATE PR
# =========================================================

def create_pull_request(
    repo_url: str,
    branch_name: str,
    title: str,
    body: str
):

    try:

        owner, repo = (
            parse_github_repo_url(
                repo_url
            )
        )

        headers = github_headers()

        info = get_repo_info(
            repo_url
        )

        default_branch = (
            info["default_branch"]
        )

        response = requests.post(
            f"https://api.github.com/repos/"
            f"{owner}/{repo}/pulls",
            headers=headers,
            json={
                "title": title,
                "body": body,
                "head": branch_name,
                "base": default_branch
            },
            timeout=30
        )

        if response.status_code not in [
            200,
            201
        ]:

            raise Exception(
                response.text
            )

        data = response.json()

        return {
            "success": True,
            "pull_request_url": (
                data["html_url"]
            ),
            "pull_request_number": (
                data["number"]
            )
        }

    except Exception as e:

        return {
            "success": False,
            "message": sanitize_error(
                str(e)
            )
        }