from llm_service import generate_migration


code = """
import pandas as pd

df = df.append(new_row)
"""

guidance = """
DataFrame.append() was removed in pandas 2.0.

Use pandas.concat() instead.

Example:

df = pd.concat([df, new_row], ignore_index=True)
"""

result = generate_migration(code, guidance)

print("MIGRATED CODE:")
print(result)