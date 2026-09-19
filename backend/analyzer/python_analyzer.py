import ast


DEPRECATED_APIS = {
    "pandas": {
        "1.x->2.x": {
            "append": {
                "replacement": "pd.concat",
                "message": "DataFrame.append() was removed in pandas 2.0",
                "severity": "high"
            },
            "iteritems": {
                "replacement": "items",
                "message": "DataFrame.iteritems() was removed in pandas 2.0",
                "severity": "medium"
            }
        }
    }
}


def parse_code(code: str):
    try:
        ast.parse(code)

        return {
            "valid": True
        }

    except SyntaxError as e:
        return {
            "valid": False,
            "error": str(e)
        }


def detect_deprecated_apis(
    code: str,
    library: str = "pandas",
    version_range: str = "1.x->2.x"
):
    try:
        tree = ast.parse(code)

    except SyntaxError as e:
        return {
            "valid": False,
            "error": str(e),
            "findings": []
        }

    findings = []

    deprecated = DEPRECATED_APIS.get(
        library,
        {}
    ).get(
        version_range,
        {}
    )

    # Check whether the target library is imported
    library_imported = False

    for node in ast.walk(tree):

        # import pandas
        # import pandas as pd
        if isinstance(node, ast.Import):

            for alias in node.names:

                if alias.name == library:
                    library_imported = True

        # from pandas import DataFrame
        elif isinstance(node, ast.ImportFrom):

            if node.module == library:
                library_imported = True

    # If library isn't imported, don't report its APIs
    if not library_imported:
        return {
            "valid": True,
            "findings": []
        }

    # Look for deprecated method calls
    for node in ast.walk(tree):

        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
        ):

            method_name = node.func.attr

            if method_name in deprecated:

                info = deprecated[method_name]

                findings.append({
                    "api": method_name,
                    "line": node.lineno,
                    "replacement": info["replacement"],
                    "message": info["message"],
                    "severity": info["severity"]
                })

    return {
        "valid": True,
        "findings": findings
    }


def verify_code(
    code: str,
    library: str = "pandas",
    version_range: str = "1.x->2.x"
):
    try:
        ast.parse(code)

    except SyntaxError as e:

        return {
            "valid": False,
            "syntax_valid": False,
            "deprecated_apis_remaining": [],
            "message": str(e)
        }

    analysis = detect_deprecated_apis(
        code=code,
        library=library,
        version_range=version_range
    )

    remaining = analysis.get(
        "findings",
        []
    )

    if remaining:

        return {
            "valid": False,
            "syntax_valid": True,
            "deprecated_apis_remaining": remaining,
            "message": "Deprecated API usage still exists in migrated code."
        }

    return {
        "valid": True,
        "syntax_valid": True,
        "deprecated_apis_remaining": [],
        "message": "Migration verification passed. No deprecated APIs detected."
    }