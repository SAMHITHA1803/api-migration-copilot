import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "backend.mcp_server.server"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Clone repository
            clone_result = await session.call_tool(
                "clone_github_repository",
                arguments={
                    "repo_url": "https://github.com/psf/requests"
                }
            )

            print("\nCLONE RESULT:\n")
            print(clone_result)

            # Extract local path
            result_text = clone_result.content[0].text

            import json

            clone_data = json.loads(result_text)
            repo_path = clone_data["local_path"]

            # Find Python files
            files_result = await session.call_tool(
                "find_repository_files",
                arguments={
                    "repo_path": repo_path
                }
            )

            print("\nREPOSITORY FILES:\n")
            print(files_result)


if __name__ == "__main__":
    asyncio.run(main())