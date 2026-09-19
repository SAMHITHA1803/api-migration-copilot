from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import traceback

from backend.migration_service import analyze_migration
from backend.agent import run_agent
from backend.applier import apply_migration
from backend.github_service import clear_workspace_root


app = FastAPI(
    title="API Migration Copilot"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:3000",
    "https://api-migration-copilot-ldza1hr9z-api-migration-copilot.vercel.app",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# Request Models
# =========================================================

class AnalyzeRequest(BaseModel):
    code: str
    library: str = "pandas"
    version_range: str = "1.x->2.x"


class RepositoryRequest(BaseModel):
    repo_url: str
    library: str = "pandas"
    version_range: str = "1.x->2.x"


class ApplyMigrationRequest(BaseModel):
    repo_path: str
    file_path: str
    migrated_code: str


# =========================================================
# Root
# =========================================================

@app.get("/")
def root():

    return {
        "message": "API Migration Copilot is running!"
    }


# =========================================================
# Direct Code Analysis
# =========================================================

@app.post("/analyze")
def analyze_code(
    request: AnalyzeRequest
):

    try:

        result = analyze_migration(
            code=request.code,
            library=request.library,
            version_range=request.version_range
        )

        return result

    except Exception as e:

        print("\n" + "=" * 70)
        print("CODE ANALYSIS ERROR")
        print("=" * 70)

        traceback.print_exc()

        print("=" * 70 + "\n")

        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


# =========================================================
# Repository Migration Agent
# =========================================================

@app.post("/migrate-repository")
async def migrate_repository(
    request: RepositoryRequest
):

    try:

        cleared_workspace = clear_workspace_root()

        print("\n")
        print("=" * 70)
        print("REPOSITORY MIGRATION REQUEST")
        print("=" * 70)

        print(
            f"Repository: {request.repo_url}"
        )

        print(
            f"Library: {request.library}"
        )

        print(
            f"Version: {request.version_range}"
        )

        print(
            f"Workspace cleared: {cleared_workspace}"
        )

        print("=" * 70)
        print()

        result = await run_agent(
            repo_url=request.repo_url,
            library=request.library,
            version_range=request.version_range
        )

        print("\n")
        print("=" * 70)
        print("REPOSITORY MIGRATION COMPLETED")
        print("=" * 70)
        print()

        return result

    except Exception as e:

        # -------------------------------------------------
        # IMPORTANT:
        # Print the COMPLETE traceback to the backend
        # terminal so we can see the actual exception.
        # -------------------------------------------------

        print("\n")
        print("=" * 70)
        print("REPOSITORY MIGRATION ERROR")
        print("=" * 70)

        print(
            f"Error type: {type(e).__name__}"
        )

        print(
            f"Error: {str(e)}"
        )

        print("\nFull traceback:")

        traceback.print_exc()

        print("=" * 70)
        print()

        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


# =========================================================
# Apply Migration
# =========================================================

@app.post("/apply-migration")
def apply_migration_endpoint(
    request: ApplyMigrationRequest
):

    try:

        result = apply_migration(
            file_path=request.file_path,
            migrated_code=request.migrated_code
        )

        return result

    except Exception as e:

        print("\n" + "=" * 70)
        print("APPLY MIGRATION ERROR")
        print("=" * 70)

        traceback.print_exc()

        print("=" * 70 + "\n")

        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }