from mcp.server import MCPServer


from backend.analyzer.python_analyzer import (
    parse_code,
    detect_deprecated_apis,
    verify_code
)

from backend.rag.retriever import load_documents

from backend.repository import (
    find_code_files,
    read_code_file
)

from backend.patcher import generate_patch

from backend.applier import apply_migration


# IMPORTANT:
# Alias the GitHub functions so they don't collide
# with the MCP tool names.

from backend.github_service import (
    clone_repository,
    create_migration_branch as git_create_migration_branch,
    commit_migration as git_commit_migration,
    push_branch as git_push_branch,
    create_pull_request as git_create_pull_request
)


# ---------------------------------------------------------
# MCP Server
# ---------------------------------------------------------

mcp = MCPServer(
    "API Migration Copilot"
)


# ---------------------------------------------------------
# Repository
# ---------------------------------------------------------

@mcp.tool()
def clone_github_repository(
    repo_url: str
) -> dict:

    return clone_repository(
        repo_url
    )


@mcp.tool()
def find_repository_files(
    repo_path: str
) -> dict:

    files = find_code_files(
        repo_path
    )

    return {
        "repository": repo_path,
        "files": files,
        "count": len(files)
    }


@mcp.tool()
def read_repository_file(
    file_path: str
) -> dict:

    try:

        code = read_code_file(
            file_path
        )

        return {
            "file": file_path,
            "content": code
        }

    except Exception as e:

        return {
            "file": file_path,
            "error": str(e)
        }


# ---------------------------------------------------------
# Static analysis
# ---------------------------------------------------------

@mcp.tool()
def parse_python_code(
    code: str
) -> dict:

    return parse_code(
        code
    )


@mcp.tool()
def detect_deprecated_api(
    code: str,
    library: str = "pandas",
    version_range: str = "1.x->2.x"
) -> dict:

    return detect_deprecated_apis(
        code=code,
        library=library,
        version_range=version_range
    )


# ---------------------------------------------------------
# RAG
# ---------------------------------------------------------

@mcp.tool()
def search_migration_docs(
    query: str,
    n_results: int = 3
) -> dict:

    retriever = load_documents()

    return retriever.search(
        query=query,
        n_results=n_results
    )


# ---------------------------------------------------------
# Verification
# ---------------------------------------------------------

@mcp.tool()
def verify_migrated_code(
    code: str,
    library: str = "pandas",
    version_range: str = "1.x->2.x"
) -> dict:

    return verify_code(
        code=code,
        library=library,
        version_range=version_range
    )


# ---------------------------------------------------------
# Patch generation
# ---------------------------------------------------------

@mcp.tool()
def generate_migration_patch(
    file_path: str,
    original_code: str,
    migrated_code: str
) -> dict:

    return generate_patch(
        file_path=file_path,
        original_code=original_code,
        migrated_code=migrated_code
    )


# ---------------------------------------------------------
# Apply migration
# ---------------------------------------------------------

@mcp.tool()
def apply_migration_to_file(
    file_path: str,
    migrated_code: str
) -> dict:

    return apply_migration(
        file_path=file_path,
        migrated_code=migrated_code
    )


# ---------------------------------------------------------
# Git branch
# ---------------------------------------------------------

@mcp.tool()
def create_migration_branch(
    repo_path: str,
    branch_name: str = "api-migration"
) -> dict:

    # IMPORTANT:
    # Call the aliased GitHub service function.
    return git_create_migration_branch(
        repo_path=repo_path,
        branch_name=branch_name
    )


# ---------------------------------------------------------
# Git commit
# ---------------------------------------------------------

@mcp.tool()
def commit_migration_changes(
    repo_path: str,
    commit_message: str = "Apply API migration"
) -> dict:

    return git_commit_migration(
        repo_path=repo_path,
        commit_message=commit_message
    )


# ---------------------------------------------------------
# Git push
# ---------------------------------------------------------

@mcp.tool()
def push_migration_branch(
    repo_path: str,
    branch_name: str
) -> dict:

    return git_push_branch(
        repo_path=repo_path,
        branch_name=branch_name
    )


# ---------------------------------------------------------
# Pull Request
# ---------------------------------------------------------

@mcp.tool()
def create_migration_pull_request(
    repo_url: str,
    branch_name: str,
    title: str,
    body: str
) -> dict:

    return git_create_pull_request(
        repo_url=repo_url,
        branch_name=branch_name,
        title=title,
        body=body
    )


# ---------------------------------------------------------
# Start server
# ---------------------------------------------------------

if __name__ == "__main__":

    mcp.run()