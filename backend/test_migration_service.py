from migration_service import analyze_migration


code = """
import pandas as pd

df = df.append(new_row)
"""


result = analyze_migration(
    code=code,
    library="pandas",
    version_range="1.x->2.x"
)

print(result)