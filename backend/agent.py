import os
import sys
import json

from dotenv import load_dotenv

from google import genai
from google.genai import types

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

load_dotenv(
    os.path.join(BASE_DIR, ".env")
)

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL_NAME = "gemini-3.5-flash-lite"


# ---------------------------------------------------------
# MCP server
# ---------------------------------------------------------

server_params = StdioServerParameters(
    command=sys.executable,
    args=[
        "-m",
        "backend.mcp_server.server"
    ],
    cwd=BASE_DIR,
)


# ---------------------------------------------------------
# MCP result conversion
# ---------------------------------------------------------

def convert_mcp_result(result) -> dict:

    structured = getattr(
        result,
        "structuredContent",
        None
    )

    if structured:
        return structured

    text_parts = []

    for item in getattr(
        result,
        "content",
        []
    ):
        if getattr(item, "type", None) == "text":
            text_parts.append(
                getattr(item, "text", "")
            )

    text_content = "\n".join(
        text_parts
    )

    if not text_content:
        return {
            "success": True
        }

    try:
        return json.loads(
            text_content
        )

    except json.JSONDecodeError:
        return {
            "result": text_content
        }


# ---------------------------------------------------------
# Gemini tool schema
# ---------------------------------------------------------

def build_gemini_tools(mcp_tools):

    declarations = []

    for tool in mcp_tools:

        schema = getattr(
            tool,
            "inputSchema",
            None
        )

        declarations.append(
            types.FunctionDeclaration(
                name=tool.name,
                description=tool.description or "",
                parameters_json_schema=schema,
            )
        )

    return [
        types.Tool(
            function_declarations=declarations
        )
    ]


# ---------------------------------------------------------
# Tool argument enrichment
# ---------------------------------------------------------

def enrich_tool_arguments(
    tool_name,
    tool_args,
    repo_url,
    repo_path,
    library,
    version_range,
    branch_name,
):

    args = dict(tool_args)

    if tool_name == "clone_github_repository":

        args["repo_url"] = repo_url

    elif tool_name == "find_repository_files":

        if not args.get("repo_path"):
            args["repo_path"] = repo_path

    elif tool_name == "read_repository_file":

        # Gemini must provide the actual file path.
        pass

    elif tool_name == "detect_deprecated_api":

        args.setdefault(
            "library",
            library
        )

        args.setdefault(
            "version_range",
            version_range
        )

    elif tool_name == "verify_migrated_code":

        args.setdefault(
            "library",
            library
        )

        args.setdefault(
            "version_range",
            version_range
        )

    elif tool_name == "create_migration_branch":

        if not args.get("repo_path"):
            args["repo_path"] = repo_path

    elif tool_name == "commit_migration_changes":

        if not args.get("repo_path"):
            args["repo_path"] = repo_path

    elif tool_name == "push_migration_branch":

        if not args.get("repo_path"):
            args["repo_path"] = repo_path

        if not args.get("branch_name"):
            args["branch_name"] = branch_name

    elif tool_name == "create_migration_pull_request":

        args["repo_url"] = repo_url

        if not args.get("branch_name"):
            args["branch_name"] = branch_name

    return args


# ---------------------------------------------------------
# Agent
# ---------------------------------------------------------

async def run_agent(
    repo_url,
    library="pandas",
    version_range="1.x->2.x",
):

    print(
        "\nSTARTING REPOSITORY "
        "MIGRATION AGENT...\n"
    )

    # -----------------------------------------------------
    # State
    # -----------------------------------------------------

    repo_path = None

    branch_created = False
    branch_name = None

    commit_created = False
    commit_hash = None

    push_succeeded = False

    pull_request_created = False
    pull_request_url = None

    files_scanned = 0

    migration_results = []

    current_file_path = None
    current_original_code = None
    current_result_index = None

    tool_trace = []

    final_text = ""

    # -----------------------------------------------------
    # MCP session
    # -----------------------------------------------------

    async with stdio_client(
        server_params
    ) as (read, write):

        async with ClientSession(
            read,
            write
        ) as session:

            await session.initialize()

            tool_list = await session.list_tools()

            gemini_tools = build_gemini_tools(
                tool_list.tools
            )

            # -------------------------------------------------
            # Agent prompt
            # -------------------------------------------------

            prompt = f"""
You are an expert software migration agent.

Repository:
{repo_url}

Library:
{library}

Version:
{version_range}

Your job is to migrate deprecated APIs in this repository.

Use the available MCP tools.

IMPORTANT:
Use the EXACT parameter names from the MCP tool schemas.

Do NOT invent parameter names such as:
- code_snippet
- migrated_code
- original_code

when the tool schema requires:
- code

===========================================================
PHASE 1 — CLONE
===========================================================

Call:

clone_github_repository

The repo_url is already known.

===========================================================
PHASE 2 — DISCOVER
===========================================================

Call:

find_repository_files

using the local_path returned from cloning.

For every Python file:

1. read_repository_file
2. detect_deprecated_api

===========================================================
PHASE 3 — DOCUMENTATION
===========================================================

For every deprecated API:

Call:

search_migration_docs

Use the returned migration documentation as authoritative
guidance.

===========================================================
PHASE 4 — MIGRATE
===========================================================

Generate migrated Python code using the original code and
the retrieved migration documentation.

Before modifying a file:

1. verify_migrated_code
2. generate_migration_patch

Only proceed when verification passes.

===========================================================
PHASE 5 — GIT
===========================================================

After verified migration:

1. create_migration_branch
2. apply_migration_to_file
3. commit_migration_changes
4. push_migration_branch
5. create_migration_pull_request

===========================================================
SAFETY RULES
===========================================================

NEVER modify main.

NEVER modify master.

NEVER commit directly to main.

NEVER push main.

NEVER create a PR from main.

If branch creation fails:
DO NOT apply migration.

If commit fails:
DO NOT push.

If push fails:
DO NOT create a pull request.

Do not invent tool results.

Do not expose secrets.

At the end provide a concise summary containing:

- files scanned
- deprecated APIs found
- migrations performed
- verification status
- migration branch
- commit hash
- push status
- pull request URL
"""

            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part(
                            text=prompt
                        )
                    ],
                )
            ]

            # Keep this reasonably low to avoid wasting
            # Gemini quota on repeated tool calls.
            max_iterations = 25

            # -------------------------------------------------
            # Agent loop
            # -------------------------------------------------

            for iteration in range(
                max_iterations
            ):

                response = await (
                    client.aio.models.generate_content(
                        model=MODEL_NAME,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            tools=gemini_tools,
                            temperature=0.1,
                        ),
                    )
                )

                function_calls = (
                    response.function_calls or []
                )

                # ---------------------------------------------
                # Final answer
                # ---------------------------------------------

                if not function_calls:

                    final_text = (
                        response.text
                        or "Migration completed."
                    )

                    break

                # ---------------------------------------------
                # Preserve Gemini assistant message
                # ---------------------------------------------

                if response.candidates:

                    contents.append(
                        response.candidates[0].content
                    )

                function_responses = []

                # ---------------------------------------------
                # Execute MCP tools
                # ---------------------------------------------

                for function_call in function_calls:

                    tool_name = function_call.name

                    raw_args = (
                        dict(function_call.args)
                        if function_call.args
                        else {}
                    )

                    tool_args = enrich_tool_arguments(
                        tool_name=tool_name,
                        tool_args=raw_args,
                        repo_url=repo_url,
                        repo_path=repo_path,
                        library=library,
                        version_range=version_range,
                        branch_name=branch_name,
                    )

                    print(
                        f"\nTOOL: {tool_name}"
                    )

                    print(
                        f"ARGS: {tool_args}"
                    )

                    # -----------------------------------------
                    # Safety gates
                    # -----------------------------------------

                    if (
                        tool_name
                        == "apply_migration_to_file"
                        and not branch_created
                    ):

                        tool_result = {
                            "success": False,
                            "blocked": True,
                            "message": (
                                "BLOCKED: No migration branch "
                                "has been successfully created."
                            ),
                        }

                    elif (
                        tool_name
                        == "commit_migration_changes"
                        and not branch_created
                    ):

                        tool_result = {
                            "success": False,
                            "blocked": True,
                            "message": (
                                "BLOCKED: Migration branch "
                                "does not exist."
                            ),
                        }

                    elif (
                        tool_name
                        == "push_migration_branch"
                        and not commit_created
                    ):

                        tool_result = {
                            "success": False,
                            "blocked": True,
                            "message": (
                                "BLOCKED: Migration changes "
                                "have not been committed."
                            ),
                        }

                    elif (
                        tool_name
                        == "create_migration_pull_request"
                        and not push_succeeded
                    ):

                        tool_result = {
                            "success": False,
                            "blocked": True,
                            "message": (
                                "BLOCKED: Migration branch "
                                "has not been successfully pushed."
                            ),
                        }

                    else:

                        try:

                            result = await session.call_tool(
                                tool_name,
                                arguments=tool_args,
                            )

                            tool_result = convert_mcp_result(
                                result
                            )

                        except Exception as e:

                            tool_result = {
                                "success": False,
                                "error": str(e),
                            }

                    print(
                        f"RESULT: {tool_result}"
                    )

                    # -----------------------------------------
                    # Save trace
                    # -----------------------------------------

                    tool_trace.append(
                        {
                            "tool": tool_name,
                            "arguments": tool_args,
                            "result": tool_result,
                        }
                    )

                    # -----------------------------------------
                    # Update agent state
                    # -----------------------------------------

                    if (
                        tool_name
                        == "clone_github_repository"
                        and tool_result.get("success")
                    ):

                        repo_path = tool_result.get(
                            "local_path"
                        )

                    elif (
                        tool_name
                        == "read_repository_file"
                        and tool_result.get("content")
                    ):

                        current_file_path = tool_result.get(
                            "file"
                        )

                        current_original_code = tool_result.get(
                            "content"
                        )

                        current_result_index = None

                    elif (
                        tool_name
                        == "find_repository_files"
                    ):

                        files_scanned = tool_result.get(
                            "count",
                            files_scanned,
                        )

                    elif (
                        tool_name
                        == "detect_deprecated_api"
                    ):

                        findings = tool_result.get(
                            "findings",
                            []
                        )

                        if findings:

                            result_entry = {
                                "file_path": current_file_path,
                                "original_code": current_original_code,
                                "findings": findings,
                            }

                            migration_results.append(
                                result_entry
                            )

                            current_result_index = (
                                len(migration_results) - 1
                            )

                    elif (
                        tool_name
                        == "verify_migrated_code"
                        and current_result_index is not None
                    ):

                        migration_results[
                            current_result_index
                        ]["verification"] = tool_result

                    elif (
                        tool_name
                        == "generate_migration_patch"
                        and current_result_index is not None
                    ):

                        migrated_code = tool_args.get(
                            "migrated_code"
                        )

                        original_code = tool_args.get(
                            "original_code"
                        )

                        if original_code:

                            migration_results[
                                current_result_index
                            ]["original_code"] = original_code

                        if migrated_code:

                            migration_results[
                                current_result_index
                            ]["migrated_code"] = migrated_code

                        migration_results[
                            current_result_index
                        ]["patch"] = tool_result.get(
                            "patch"
                        )

                        migration_results[
                            current_result_index
                        ]["migrated_code"] = tool_result.get(
                            "migrated_code"
                        )

                        migration_results[
                            current_result_index
                        ]["patch_changed"] = tool_result.get(
                            "changed"
                        )

                    elif (
                        tool_name
                        == "apply_migration_to_file"
                        and current_result_index is not None
                    ):

                        migrated_code = tool_args.get(
                            "migrated_code"
                        )

                        if migrated_code:

                            migration_results[
                                current_result_index
                            ]["migrated_code"] = migrated_code

                        migration_results[
                            current_result_index
                        ]["apply_result"] = tool_result

                    elif (
                        tool_name
                        == "create_migration_branch"
                    ):

                        if tool_result.get("success"):

                            branch_created = True

                            branch_name = (
                                tool_result.get(
                                    "branch_name"
                                )
                            )

                        else:

                            branch_created = False

                    elif (
                        tool_name
                        == "commit_migration_changes"
                    ):

                        if tool_result.get("success"):

                            commit_created = True

                            commit_hash = (
                                tool_result.get(
                                    "commit_hash"
                                )
                            )

                        else:

                            commit_created = False

                    elif (
                        tool_name
                        == "push_migration_branch"
                    ):

                        push_succeeded = bool(
                            tool_result.get(
                                "success"
                            )
                        )

                    elif (
                        tool_name
                        == "create_migration_pull_request"
                    ):

                        pull_request_created = bool(
                            tool_result.get(
                                "success"
                            )
                        )

                        if pull_request_created:

                            pull_request_url = (
                                tool_result.get(
                                    "pull_request_url"
                                )
                            )

                    # -----------------------------------------
                    # Gemini function response
                    #
                    # IMPORTANT:
                    # Gemini rejects role="tool".
                    # Function responses are sent as role="user".
                    # -----------------------------------------

                    function_responses.append(
                        types.Part.from_function_response(
                            name=tool_name,
                            response=tool_result,
                        )
                    )

                contents.append(
                    types.Content(
                        role="user",
                        parts=function_responses,
                    )
                )

            else:

                final_text = (
                    "Agent stopped after reaching "
                    "the maximum number of iterations."
                )

    # ---------------------------------------------------------
    # Git result
    # ---------------------------------------------------------

    git_result = {
        "branch_created": branch_created,
        "branch_name": branch_name,
        "commit_created": commit_created,
        "commit_hash": commit_hash,
        "push_succeeded": push_succeeded,
        "pull_request_created": pull_request_created,
        "pull_request_url": pull_request_url,
    }

    # ---------------------------------------------------------
    # Overall result
    # ---------------------------------------------------------

    overall_success = (
        branch_created
        and commit_created
        and push_succeeded
        and pull_request_created
    )

    return {
        "success": overall_success,
        "repository": repo_url,
        "local_path": repo_path,
        "files_scanned": files_scanned,
        "results": migration_results,
        "git": git_result,
        "tool_trace": tool_trace,
        "agent_summary": final_text,
    }