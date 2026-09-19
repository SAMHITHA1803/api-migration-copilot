import difflib


def generate_patch(
    file_path: str,
    original_code: str,
    migrated_code: str
) -> dict:

    diff = difflib.unified_diff(
        original_code.splitlines(),
        migrated_code.splitlines(),
        fromfile=file_path,
        tofile=file_path,
        lineterm=""
    )

    patch = "\n".join(diff)

    return {
        "file": file_path,
        "changed": original_code != migrated_code,
        "patch": patch,
        "original_code": original_code,
        "migrated_code": migrated_code
    }