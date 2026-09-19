from analyzer.python_analyzer import detect_deprecated_apis


code = """
import pandas as pd

df = pd.DataFrame({"price": [10, 20, 30]})

new_row = pd.DataFrame({"price": [40]})

df = df.append(new_row)

print(df)
"""


result = detect_deprecated_apis(code)

print(result)