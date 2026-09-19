from backend.analyzer.python_analyzer import (
    detect_deprecated_apis,
    verify_code
)

from backend.rag.retriever import load_documents

from backend.llm_service import generate_migration

from backend.patcher import generate_patch


def analyze_migration(
    code: str,
    library: str = "pandas",
    version_range: str = "1.x->2.x",
    file_path: str = "migration.py"
):

    analysis = detect_deprecated_apis(
        code=code,
        library=library,
        version_range=version_range
    )

    if not analysis["valid"]:

        return analysis

    # Nothing to migrate
    if not analysis["findings"]:

        return {
            "valid": True,
            "findings": [],
            "migration_guidance": [],
            "migrated_code": code,

            "verification": verify_code(
                code,
                library=library,
                version_range=version_range
            ),

            "patch": {
                "file": file_path,
                "changed": False,
                "patch": ""
            }
        }

    retriever = load_documents()

    migration_guidance = []

    for finding in analysis["findings"]:

        query = (
            f"How should {library} "
            f"{finding['api']} "
            f"be migrated from "
            f"{version_range}?"
        )

        results = retriever.search(
            query=query,
            n_results=1
        )

        documents = results.get(
            "documents",
            []
        )

        documentation = ""

        if documents and documents[0]:

            documentation = documents[0][0]

        migration_guidance.append({
            "api": finding["api"],
            "query": query,
            "documentation": documentation
        })

    guidance_text = "\n\n".join(
        item["documentation"]
        for item in migration_guidance
    )

    migrated_code = generate_migration(
        code=code,
        migration_guidance=guidance_text
    )

    verification = verify_code(
        migrated_code,
        library=library,
        version_range=version_range
    )

    patch = generate_patch(
        file_path=file_path,
        original_code=code,
        migrated_code=migrated_code
    )

    return {
        "valid": True,
        "findings": analysis["findings"],
        "migration_guidance": migration_guidance,
        "migrated_code": migrated_code,
        "verification": verification,
        "patch": patch
    }